from tests import run_tests


def read_queries_from_file(filepath):
    queries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(line)
    return queries


if __name__ == "__main__":
    tests = read_queries_from_file("queries.txt")
    run_tests(tests)
