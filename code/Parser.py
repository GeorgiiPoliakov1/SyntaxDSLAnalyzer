import pymorphy3


morph = pymorphy3.MorphAnalyzer()


class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, node):
        self.children.append(node)


def is_imperative_verb(word):
    for p in morph.parse(word):
        if "VERB" in p.tag and "impr" in p.tag:
            return True
    return False


def is_noun(word):
    for p in morph.parse(word):
        if "NOUN" in p.tag:
            return True
    return False


def is_genitive(word):
    for p in morph.parse(word):
        if "NOUN" in p.tag and "gent" in p.tag:
            return True
    return False


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, parent):
        token = self.current()
        if token is None:
            raise SyntaxError("Неожиданный конец запроса")
        parent.add(Node(token))
        self.pos += 1
        return token

    def expect(self, parent, token):
        if self.current() != token:
            raise SyntaxError(
                f"Ошибка на токене '{self.current()}', ожидалось '{token}'"
            )
        self.consume(parent)

    def parse_query(self):
        node = Node("query")
        node.add(self.parse_action())
        node.add(self.parse_object())
        node.add(self.parse_filters())
        return node

    def parse_action(self):
        node = Node("action")
        word = self.current()
        if word is None:
            raise SyntaxError("Ожидался глагол")
        if not is_imperative_verb(word):
            raise SyntaxError(
                f"'{word}' не является глаголом в повелительном наклонении"
            )
        self.consume(node)
        return node

    def parse_object(self):
        node = Node("object")
        node.add(self.parse_object_type())
        node.add(self.parse_object_name())
        return node

    def parse_object_type(self):
        node = Node("objectType")
        token = self.current()
        if token not in ["документы", "приказы", "договоры"]:
            raise SyntaxError(f"Ошибка на токене '{token}', ожидался тип объекта")
        self.consume(node)
        return node

    def parse_object_name(self):
        node = Node("objectName")
        if self.current() == "под":
            node.add(self.parse_by_title())
        if self.current() == "по":
            node.add(self.parse_by_number())
        return node

    def parse_by_title(self):
        node = Node("byTitle")
        self.expect(node, "под")
        self.expect(node, "названием")
        node.add(self.parse_title_name())
        return node

    def parse_title_name(self):
        node = Node("titleName")
        self.expect(node, "«")
        while True:
            token = self.current()
            if token is None:
                raise SyntaxError("Не закрыты кавычки")
            if token == "»":
                break
            self.consume(node)
        self.expect(node, "»")
        if self.current() == ",":
            self.expect(node, ",")
            node.add(self.parse_title_name())
        return node

    def parse_by_number(self):
        node = Node("byNumber")
        self.expect(node, "по")
        self.expect(node, "номеру")
        node.add(self.parse_number_body())
        return node

    def parse_number_body(self):
        node = Node("numberBody")
        if self.current() is None or not self.current().isdigit():
            raise SyntaxError("Ожидалось число")
        self.consume(node)
        if self.current() == ",":
            self.expect(node, ",")
            node.add(self.parse_number_body())
        return node

    def parse_filters(self):
        node = Node("filters")
        while self.current() in ["от", "с", "по", "из", "за"]:
            node.add(self.parse_filter())
        return node

    def parse_filter(self):
        token = self.current()
        if token == "от":
            return self.parse_author()
        if token in ["с"]:
            return self.parse_theme()
        if token == "из":
            return self.parse_source()
        if token == "за":
            return self.parse_time_range()
        raise SyntaxError(f"Неизвестный фильтр '{token}'")

    def parse_author(self):
        node = Node("author")
        self.expect(node, "от")
        node.add(self.parse_author_name())
        return node

    def parse_author_name(self):
        node = Node("authorName")
        word1 = self.current()
        if not is_genitive(word1):
            raise SyntaxError(
                f"'{word1}' должно быть существительным в родительном падеже"
            )
        self.consume(node)
        word2 = self.current()
        if not is_genitive(word2):
            raise SyntaxError(
                f"'{word2}' должно быть существительным в родительном падеже"
            )
        self.consume(node)
        if self.current() == ",":
            self.expect(node, ",")
            node.add(self.parse_author_name())
        return node

    def parse_theme(self):
        node = Node("theme")
        if self.current() == "с":
            self.expect(node, "с")
            self.expect(node, "темой")
        node.add(self.parse_theme_name())
        return node

    def parse_theme_name(self):
        node = Node("themeName")
        word = self.current()
        if not is_noun(word):
            raise SyntaxError(f"'{word}' должно быть существительным")
        self.consume(node)
        if self.current() == ",":
            self.expect(node, ",")
            node.add(self.parse_theme_name())
        return node

    def parse_source(self):
        node = Node("source")
        self.expect(node, "из")
        word = self.current()
        if not is_genitive(word):
            raise SyntaxError(
                f"'{word}' должно быть существительным в родительном падеже"
            )
        self.consume(node)
        if self.current() is None or not self.current().isdigit():
            raise SyntaxError("Ожидался номер источника")
        self.consume(node)
        return node

    def parse_time_range(self):
        node = Node("timeRange")
        self.expect(node, "за")
        node.add(self.parse_time())
        return node

    def parse_time(self):
        node = Node("time")
        if self.current() is None or not self.current().isdigit():
            raise SyntaxError("Ожидался год (число)")
        self.consume(node)
        if self.current() == "или":
            self.expect(node, "или")
            node.add(self.parse_time())
        elif self.current() == "год":
            self.expect(node, "год")
        else:
            raise SyntaxError("Ожидалось 'или' или 'год'")
        return node
