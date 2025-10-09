import pandas as pd
import gzip
import argparse

def load_tsv(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return pd.read_csv(f, sep="\t", low_memory=False)
    else:
        return pd.read_csv(path, sep="\t", low_memory=False)

def main():
    parser = argparse.ArgumentParser(description="Combina datasets do IMDb em um CSV.")
    parser.add_argument("--basics", required=True)
    parser.add_argument("--ratings", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min_votes", type=int, default=1000)
    args = parser.parse_args()

    print("🔹 Lendo arquivos...")
    basics = load_tsv(args.basics)
    ratings = load_tsv(args.ratings)

    print("🔹 Combinando datasets...")
    movies = pd.merge(basics, ratings, on="tconst")
    movies = movies[movies["numVotes"] >= args.min_votes]

    movies.to_csv(args.output, index=False)
    print(f"✅ Arquivo salvo em: {args.output}")

if __name__ == "__main__":
    main()
