
import pymysql
from py2neo import Graph, Node, Relationship
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Insert Category
def insert_category(cursor, name, level=1, parent_id=None, description=None):
    query = """
    INSERT INTO Categories (category_name, level, parent_category_id, description)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (name, level, parent_id, description))

# 2. Add Synonym
def add_synonym(cursor, term_id, synonym, similarity_score=None, notes=None):
    query = """
    INSERT INTO TermSynonyms (term_id, synonym, similarity_score, notes)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (term_id, synonym, similarity_score, notes))

# 3. Create Term Relation
def create_term_relation(cursor, term1_id, term2_id, relation_type, subtype=None, strength=None, bidirectional=False, description=None):
    query = """
    INSERT INTO TermRelations (term1_id, term2_id, relation_type, relation_subtype, strength, bidirectional, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (term1_id, term2_id, relation_type, subtype, strength, bidirectional, description))

# 4. Add Tag
def add_tag(cursor, tag_name, description=None):
    cursor.execute("INSERT IGNORE INTO Tags (tag_name, description) VALUES (%s, %s)", (tag_name, description))

def link_tag_to_term(cursor, term_id, tag_name):
    cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = %s", (tag_name,))
    tag_id = cursor.fetchone()
    if tag_id:
        query = "INSERT IGNORE INTO TermTags (term_id, tag_id) VALUES (%s, %s)"
        cursor.execute(query, (term_id, tag_id[0]))

# 5. Sync Terms to Neo4j
def sync_terms_to_neo4j(graph, terms_df, relations_df):
    graph.delete_all()
    term_nodes = {}
    for _, term in terms_df.iterrows():
        node = Node("Term", term_id=term['term_id'], name=term['term'], category=term['category_id'], description=term['description'])
        graph.create(node)
        term_nodes[term['term_id']] = node

    for _, rel in relations_df.iterrows():
        rel_node = Relationship(
            term_nodes[rel['term1_id']],
            rel['relation_type'],
            term_nodes[rel['term2_id']],
            subtype=rel['relation_subtype'],
            strength=rel['strength'],
            description=rel['description']
        )
        graph.create(rel_node)

# 6. NLP-based Similar Term Extraction
def extract_and_store_similar_terms(conn, terms_df, threshold=0.5):
    okt = Okt()
    terms_df['nouns'] = terms_df['description'].apply(lambda x: [n for n in okt.nouns(x) if len(n) > 1])
    terms_df['noun_text'] = terms_df['nouns'].apply(lambda x: ' '.join(x))

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(terms_df['noun_text'])
    sim_matrix = cosine_similarity(tfidf_matrix)

    cursor = conn.cursor()
    for i in range(len(terms_df)):
        for j in range(i + 1, len(terms_df)):
            sim_score = sim_matrix[i, j]
            if sim_score >= threshold:
                query = """
                INSERT INTO TermRelations (term1_id, term2_id, relation_type, relation_subtype, strength, description)
                VALUES (%s, %s, 'similarity', 'auto-detected', %s, %s)
                """
                cursor.execute(query, (
                    terms_df.loc[i, 'term_id'],
                    terms_df.loc[j, 'term_id'],
                    sim_score,
                    f"자동 감지된 유사도: {sim_score:.2f}"
                ))
    conn.commit()
    cursor.close()

# 7. Normalize Attributes
def normalize_attributes(cursor, term_id, attributes: dict):
    for name, value in attributes.items():
        cursor.execute("""
            INSERT INTO TermAttributes (term_id, attribute_name, attribute_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE attribute_value = %s
        """, (term_id, name, value, value))
