"""
Encode arxiv paper embeddings (title + abstract) and save each as a .npy file.

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


def encode_and_save(
    input_path: str,
    output_dir: str,
    model_name: str = "/workspace/bge-m3",
    batch_size: int = 64,
    num_workers: int = 4,
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

    # Load model
    print(f"Loading model: {model_name} ...")
    model = SentenceTransformer(model_name)

    # Process in batches
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"Processing {len(df)} papers in {total_batches} batches (batch_size={batch_size}) ...")

    for batch_start in tqdm(range(0, len(df), batch_size), total=total_batches, desc="Encoding"):
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
            # Replace '/' in id with '_' to avoid path issues (e.g., "0704.0001")
            safe_id = str(paper_id).replace("/", "_")
            npy_path = os.path.join(output_dir, f"{safe_id}.npy")
            np.save(npy_path, embeddings[i])

    print(f"Done! All embeddings saved to {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encode arxiv paper embeddings")
    parser.add_argument("--input", type=str, default="arxiv-metadata-oai-snapshot.parquet",
                        help="Path to the parquet file")
    parser.add_argument("--output-dir", type=str, default="embeddings",
                        help="Directory to save .npy files")
    parser.add_argument("--batch-size", type=int, default=512,
                        help="Batch size for encoding")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2",
                        help="Sentence transformer model name")
    parser.add_argument("--num-workers", type=int, default=4,
                        help="Number of data loading workers")
    args = parser.parse_args()

    encode_and_save(
        input_path=args.input,
        output_dir=args.output_dir,
        model_name=args.model,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
# python encode_embeddings.py --input arxiv-metadata-oai-snapshot.parquet --output-dir embeddings --batch-size 512
