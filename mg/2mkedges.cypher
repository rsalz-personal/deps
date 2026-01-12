LOAD CSV FROM "file:///edges.csv" WITH HEADER AS row
    MATCH (a:Node {id: row.from}), (b:Node {id: row.to})
    MERGE (a)-[:DEPENDS_ON]->(b);
