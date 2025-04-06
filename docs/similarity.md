# Using Node Similarity for Business Entity Resolution

## Business Case: Identifying Re-registered Businesses

Banks and financial institutions often face the challenge of identifying businesses that have been re-registered under different names. This information is valuable for:

- Cross-selling products that were successful with the original business
- Risk assessment based on previous business history
- Marketing and customer relationship management
- Fraud detection and prevention

The key insight is that even when a business is re-registered under a different name, it often maintains similar transaction patterns with suppliers, customers, and partners.

## How Jaccard Similarity Helps

Jaccard similarity in a transaction graph compares the "neighborhood" of each business entity - who they transact with. If two businesses share many common transaction partners relative to their total number of partners, they might be the same business operating under different names.

The Jaccard similarity coefficient is calculated as:
```
similarity = |A ∩ B| / |A ∪ B|
```
where A and B are the sets of transaction partners for each business.

## Implementation with IbisGraph

Here's how to implement this analysis using IbisGraph while keeping all data processing within your data warehouse:

```python
import ibis
import ibisgraph as ig

# Connect to your database (e.g., PostgreSQL)
conn = ibis.postgres.connect(
    host='your_host',
    database='your_db',
    user='your_user',
    password='your_password'
)

# Assuming you have a table of transactions
# transactions_table:
#   - source_id: business initiating the transaction
#   - target_id: business receiving the transaction
#   - amount: transaction amount
#   - date: transaction date

# Create a graph from recent transactions (e.g., last 6 months)
transactions = conn.table('transactions_table')
recent_txns = transactions.filter(
    transactions.date >= '2024-10-01'
)

# Create a graph from the transactions
graph = ig.Graph(
    recent_txns,
    source_col='source_id',
    target_col='target_id'
)

# Calculate Jaccard similarity between all pairs of businesses
similarity = graph.node_similarity(method='jaccard')

# Filter for highly similar pairs (e.g., similarity > 0.7)
potential_matches = similarity.filter(similarity.similarity > 0.7)

# If you have business metadata table
business_info = conn.table('business_info')

# Join with business information for analysis
results = (
    potential_matches
    .join(
        business_info.alias('b1'),
        potential_matches.node1 == business_info.business_id
    )
    .join(
        business_info.alias('b2'),
        potential_matches.node2 == business_info.business_id
    )
    .select([
        'node1',
        'node2',
        'similarity',
        'b1.business_name',
        'b1.registration_date',
        'b2.business_name',
        'b2.registration_date'
    ])
)

# Execute and get results
matches = results.execute()
```

## Interpreting Results

The results will show pairs of businesses with similar transaction patterns. To identify potential re-registrations, look for:

1. High similarity score (e.g., > 0.7)
2. Different registration dates
3. Similar business names or addresses (if available)
4. One business being inactive when the other becomes active

## Additional Considerations

To improve the accuracy of matching:

1. **Time Windows**: Compare transaction patterns within specific time windows to account for seasonal businesses

```python
# Example: Compare patterns in similar seasons
q1_2024 = transactions.filter(
    (transactions.date >= '2024-01-01') &
    (transactions.date < '2024-04-01')
)
q1_2023 = transactions.filter(
    (transactions.date >= '2023-01-01') &
    (transactions.date < '2023-04-01')
)

# Create separate graphs and compare
graph_2024 = ig.Graph(q1_2024, source_col='source_id', target_col='target_id')
graph_2023 = ig.Graph(q1_2023, source_col='source_id', target_col='target_id')
```

2. **Transaction Amounts**: Weight edges by transaction amounts to give more importance to significant business relationships

```python
# Create a weighted graph
weighted_graph = ig.Graph(
    recent_txns,
    source_col='source_id',
    target_col='target_id',
    weight_col='amount'
)
```

3. **Filter Noise**: Remove very common transaction partners (e.g., utility companies) that might create false similarities

```python
# Remove high-degree nodes (common transaction partners)
degrees = graph.degrees()
filtered_txns = recent_txns.filter(
    ~recent_txns.target_id.isin(
        degrees.filter(degrees.degree > 1000).node_id
    )
)
```

## Benefits of Using IbisGraph

1. **Data Privacy**: All processing happens within your data warehouse - sensitive transaction data never leaves your secure environment
2. **Scalability**: Leverages your database's built-in optimization capabilities
3. **Real-time Analysis**: Can be integrated into regular monitoring processes
4. **Easy Integration**: Works with existing data warehouse infrastructure

This approach helps identify business opportunities while maintaining data security and leveraging existing infrastructure. The results can be used by:
- Sales teams for cross-selling
- Risk teams for credit assessment
- Compliance teams for fraud detection
- Marketing teams for targeted campaigns
