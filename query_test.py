from app.memory.query_extractor import QueryExctractor

q = QueryExctractor()

print(q.extract("what is my city?"))
print(q.extract("what is my favorite language"))