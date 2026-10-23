"""
Neo4j Database Connection
Manages connection to the expert knowledge graph
"""

import certifi
from neo4j import GraphDatabase, TrustCustomCAs
from contextlib import contextmanager
from typing import Optional

from app.config import settings


class Neo4jConnection:
    """Neo4j connection manager"""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None
    ):
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self._driver = None

    @property
    def driver(self):
        """Lazy initialization of driver"""
        if self._driver is None:
            if self.uri.startswith(("neo4j+s://", "bolt+s://")):
                # Encrypted (e.g. AuraDB): verify against certifi's CA bundle, since the
                # OS store may lack the root (Windows fetches some roots only on demand)
                scheme, address = self.uri.split("+s://", 1)
                self._driver = GraphDatabase.driver(
                    f"{scheme}://{address}",
                    auth=(self.user, self.password),
                    encrypted=True,
                    trusted_certificates=TrustCustomCAs(certifi.where())
                )
            else:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
        return self._driver

    def close(self):
        """Close the driver connection"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Check if connection is working"""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Neo4j connection error: {e}")
            return False

    @contextmanager
    def session(self):
        """Context manager for Neo4j sessions"""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()

    def run_query(self, query: str, parameters: dict = None) -> list:
        """Execute a Cypher query and return results"""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def run_write_query(self, query: str, parameters: dict = None):
        """Execute a write query with transaction"""
        with self.session() as session:
            result = session.execute_write(
                lambda tx: tx.run(query, parameters or {}).consume()
            )
            return result


# Singleton instance
_neo4j_connection: Optional[Neo4jConnection] = None


def get_neo4j() -> Neo4jConnection:
    """Get or create Neo4j connection instance"""
    global _neo4j_connection
    if _neo4j_connection is None:
        _neo4j_connection = Neo4jConnection()
    return _neo4j_connection


def close_neo4j():
    """Close Neo4j connection"""
    global _neo4j_connection
    if _neo4j_connection is not None:
        _neo4j_connection.close()
        _neo4j_connection = None
