from Parser import Parser
import os
import shutil
from graphviz import Digraph
import re


def tokenize(text):
    return re.findall(r"«|»|,|[а-яa-z0-9]+", text.lower())


def draw_tree(node, filename):
    graph = Digraph()
    counter = 0

    def walk(n, parent=None):
        nonlocal counter
        node_id = str(counter)
        counter += 1
        graph.node(node_id, n.name)
        if parent is not None:
            graph.edge(parent, node_id)
        for child in n.children:
            walk(child, node_id)

    walk(node)
    graph.render(filename, format="png", cleanup=True)


def prepare_results_folder():
    base = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base, "..", "results")
    if os.path.exists(results_path):
        shutil.rmtree(results_path)
    os.makedirs(results_path)
    return results_path


def analyze_query(text, index, results_dir):
    print("\nИсходный запрос:")
    print(text)
    tokens = tokenize(text)
    try:
        parser = Parser(tokens)
        tree = parser.parse_query()
        print("Синтаксический анализ: УСПЕХ")
        filename = os.path.join(results_dir, f"tree_{index}")
        draw_tree(tree, filename)
    except SyntaxError as e:
        print("Синтаксический анализ: ОШИБКА")
        print(e)


def run_tests(tests):
    results_dir = prepare_results_folder()
    for i, q in enumerate(tests, 1):
        analyze_query(q, i, results_dir)
