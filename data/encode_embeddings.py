"""
Encode arxiv paper embeddings (title + abstract) and save each as a .npy file.
Supports dual-GPU parallel processing for faster encoding.

Usage:
    python encode_embeddings.py [--input arxiv-metadata-oai-snapshot.parquet]
                                [--output-dir embeddings]
                                [--batch-size 512]
                                [--model all-MiniLM-L6-v2]
                                [--num-workers 4]
"""

import argparse
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch.multiprocessing as mp


def _worker(gpu_id: int, df: pd.DataFrame, output_dir: str, model_name: str, batch_size: int):
    """Worker function that runs on a single GPU to encode its share of documents."""
    import torch
    device = f"cuda:{gpu_id}"

    print(f"[GPU {gpu_id}] Loading model: {model_name} ...")
    model = SentenceTransformer(model_name, device=device)

    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"[GPU {gpu_id}] Processing {len(df)} papers in {total_batches} batches (batch_size={batch_size}) ...")

    for batch_start in tqdm(range(0, len(df), batch_size), total=total_batches, desc=f"GPU {gpu_id}"):
        batch_end = min(batch_start + batch_size, len(df))
        batch_df = df.iloc[batch_start:batch_end]

        # Combine title + abstract
        sentences = []
        for _, row in batch_df.iterrows():
            title = str(row["title"]).strip() if pd.notna(row["title"]) else ""
            abstract = str(row["abstract"]).strip() if pd.notna(row["abstract"]) else ""
            text = f"{title}. {abstract}" if abstract else title
            sentences.append(text)

        # Encode batch
        embeddings = model.encode(
            sentences,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        # Save each embedding as a separate .npy file
        ids = batch_df["id"].values
        for i, paper_id in enumerate(ids):
            safe_id = str(paper_id).replace("/", "_")
            npy_path = os.path.join(output_dir, f"{safe_id}.npy")
            np.save(npy_path, embeddings[i])

    print(f"[GPU {gpu_id}] Done!")


def encode_and_save(
    input_path: str,
    output_dir: str,
    model_name: str = "/workspace/bge-m3",
    batch_size: int = 64,
    num_workers: int = 4,
    merged_output: str = "embeddings/embeddings.npy",
):
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print(f"Loading data from {input_path} ...")
    df = pd.read_parquet(input_path)
    print(f"Total papers: {len(df)}")

    # Check which IDs already have embeddings (for resuming)
    existing = set()
    if os.path.exists(output_dir):
        for fname in os.listdir(output_dir):
            if fname.endswith(".npy"):
                existing.add(fname[:-4])  # strip .npy
    if existing:
        print(f"Found {len(existing)} existing embeddings, skipping them.")

    # Filter out already-processed papers
    mask = ~df["id"].isin(existing)
    df = df[mask].reset_index(drop=True)
    print(f"Papers to process: {len(df)}")

    if len(df) == 0:
        print("All papers already processed. Done!")
        return

    # Split data into two halves for dual-GPU processing
    mid = len(df) // 2
    df_gpu0 = df.iloc[:mid].reset_index(drop=True)
    df_gpu1 = df.iloc[mid:].reset_index(drop=True)

    print(f"Splitting data: GPU 0 gets {len(df_gpu0)} papers, GPU 1 gets {len(df_gpu1)} papers")

    # Launch two processes, one per GPU
    mp.set_start_method("spawn", force=True)
    p0 = mp.Process(target=_worker, args=(0, df_gpu0, output_dir, model_name, batch_size))
    p1 = mp.Process(target=_worker, args=(1, df_gpu1, output_dir, model_name, batch_size))

    p0.start()
    p1.start()

    p0.join()
    p1.join()

    print(f"Done! All embeddings saved to {output_dir}/")

    # Merge all per-paper .npy files into a single embeddings.npy
    merge_embeddings(input_path, output_dir, merged_output)


def merge_embeddings(input_path: str, embeddings_dir: str, merged_output: str):
    """
    将每个 paper 的单独 .npy 文件按照 parquet 中的行顺序合并为一个 embeddings.npy 文件。
    
    Args:
        input_path: parquet 文件路径（用于确定行顺序）
        embeddings_dir: 存放各个 {paper_id}.npy 的目录
        merged_output: 合并后的输出文件路径
    """
    print(f"Merging embeddings from {embeddings_dir} ...")
    df = pd.read_parquet(input_path, columns=["id"])
    paper_ids = df["id"].astype(str).values
    print(f"Total papers in parquet: {len(paper_ids)}")

    # 先读一个文件来确定 embedding 维度
    sample_file = None
    for pid in paper_ids:
        safe_id = pid.replace("/", "_")
        p = os.path.join(embeddings_dir, f"{safe_id}.npy")
        if os.path.exists(p):
            sample_file = p
            break

    if sample_file is None:
        print("Error: No embedding files found!")
        return

    sample_emb = np.load(sample_file)
    emb_dim = sample_emb.shape[0]
    print(f"Embedding dimension: {emb_dim}")

    # 按 parquet 行顺序逐个加载，缺失则填零向量
    all_embeddings = np.zeros((len(paper_ids), emb_dim), dtype=np.float32)
    missing = 0
    for i, pid in enumerate(tqdm(paper_ids, desc="Merging")):
        safe_id = pid.replace("/", "_")
        p = os.path.join(embeddings_dir, f"{safe_id}.npy")
        if os.path.exists(p):
            all_embeddings[i] = np.load(p)
        else:
            missing += 1

    if missing > 0:
        print(f"Warning: {missing} papers have no embedding (filled with zeros)")

    np.save(merged_output, all_embeddings)
    print(f"Merged embeddings saved to {merged_output}  shape={all_embeddings.shape}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encode arxiv paper embeddings")
    parser.add_argument("--input", type=str, default="arxiv-metadata-oai-snapshot.parquet",
                        help="Path to the parquet file")
    parser.add_argument("--output-dir", type=str, default="embeddings",
                        help="Directory to save individual .npy files")
    parser.add_argument("--merged-output", type=str, default="embeddings/embeddings.npy",
                        help="Path to save the merged embeddings.npy")
    parser.add_argument("--batch-size", type=int, default=512,
                        help="Batch size for encoding")
    parser.add_argument("--model", type=str, default="/workspace/bge-m3",
                        help="Sentence transformer model name")
    parser.add_argument("--num-workers", type=int, default=4,
                        help="Number of data loading workers")
    parser.add_argument("--merge-only", action="store_true",
                        help="Skip encoding, only merge existing .npy files")
    args = parser.parse_args()

    if args.merge_only:
        merge_embeddings(args.input, args.output_dir, args.merged_output)
    else:
        encode_and_save(
            input_path=args.input,
            output_dir=args.output_dir,
            model_name=args.model,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            merged_output=args.merged_output,
        )
# python encode_embeddings.py --input arxiv-metadata-oai-snapshot.parquet --output-dir embeddings --batch-size 32
# python encode_embeddings.py --input arxiv-metadata-oai-snapshot.parquet --output-dir embeddings --merge-only
