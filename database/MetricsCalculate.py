from database.Neo4jConnection import Neo4jConnection

"""
    Класс содержащий query для вычисления метрик сети 
"""


class MetricsCalculate:
    def __init__(self, metric_name, write_property):
        self.metric_name = metric_name
        self.write_property = write_property
        self.connection = Neo4jConnection()

    def metric_calculate(
            self,
            graph_name,
            relationship_weight_property
    ):
        # Validate relationship weight values before running GDS algorithms
        # to avoid incorrect results when weights are negative.
        # Query DB for min/max of the provided weight property across all rels.
        conn = self.connection
        try:
            validate_q = f"MATCH ()-[r]->() WHERE r.{relationship_weight_property} IS NOT NULL RETURN min(r.{relationship_weight_property}) AS minVal, max(r.{relationship_weight_property}) AS maxVal"
            stats = conn.run(validate_q)
        except Exception:
            stats = None

        # If we got a result, inspect minVal
        try:
            if stats and len(stats) > 0:
                row = stats[0]
                # row may be a dict-like record or a list depending on driver wrapper
                min_val = None
                if isinstance(row, dict):
                    min_val = row.get('minVal')
                else:
                    # try to access by attribute or index
                    try:
                        min_val = row['minVal']
                    except Exception:
                        try:
                            min_val = row[0]
                        except Exception:
                            min_val = None

                if min_val is not None:
                    try:
                        if float(min_val) < 0:
                            raise ValueError(f"Negative relationship weight detected for property '{relationship_weight_property}': min={min_val}. Shortest-path based GDS algorithms (betweenness) require non-negative weights.")
                    except ValueError:
                        raise
                    except Exception:
                        # Could not interpret min_val as numeric — ignore and proceed
                        pass
        except Exception:
            # any error during validation should not block execution; proceed to calculation
            pass

        return self.__metric_calculate(graph_name, relationship_weight_property)

    def __metric_calculate(self, graph_name, weight_property):
        query = f'''
            CALL gds.{self.metric_name}.write(
                '{graph_name}',
                {{
                relationshipWeightProperty: '{weight_property}',
                writeProperty: '{self.write_property}'
                }}
            )
        '''
        return self.connection.run(query)


class Betweenness(MetricsCalculate):
    def __init__(self):
        super().__init__("betweenness", "betweenness")


class PageRank(MetricsCalculate):
    def __init__(self):
        super().__init__("pageRank", "pageRank")
