CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY, 
    type TEXT, 
    name TEXT, 
    url TEXT, 
    rendered BOOLEAN, 
    uploaded BOOLEAN, 
    description TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY, 
    name TEXT, 
    data BLOB, 
    ext TEXT, 
    description TEXT
);
