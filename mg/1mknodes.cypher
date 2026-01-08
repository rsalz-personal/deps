LOAD CSV FROM "file:///nodes.csv" WITH HEADER AS row
MERGE (n:Node {id: row.id})
SET n.name = row.name,
    n.when = row.when,
    n.who  = row.who,
    n.type = row.type;
