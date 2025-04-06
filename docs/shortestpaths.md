# Using Shortest Paths for Risk Assessment and Compliance

## Business Case: Transaction Network Risk Analysis

Financial institutions need to assess the risk of new customers by understanding their potential connections to known high-risk entities. In a transaction network:
- Nodes represent entities (individuals or businesses)
- Edges represent transactions or other relationships
- Some nodes are flagged as high-risk (blacklisted)

The key insight is that entities closer to high-risk nodes in the transaction network may pose greater risk themselves.

## Why Shortest Paths Matter

The shortest path between two entities in a transaction network represents:
- The minimum number of intermediaries needed to connect them
- The most direct potential influence or relationship path
- A quantifiable measure of "relationship distance"

This analysis helps:
- Score new customers based on proximity to high-risk entities
- Identify potential money laundering routes
- Assess indirect exposure to sanctioned entities
- Support Know Your Customer (KYC) processes

## Implementation with IbisGraph in Snowflake

Here's how to implement this analysis using IbisGraph while keeping all processing within Snowflake:

```python
import ibis
import ibisgraph as ig

# Connect to Snowflake
conn = ibis.snowflake.connect(
    user='YOUR_USER',
    password='YOUR_PASSWORD',
    account='YOUR_ACCOUNT',
    database='YOUR_DATABASE',
    schema='YOUR_SCHEMA'
)

# Assume we have these tables in Snowflake:
# - TRANSACTIONS: Historical transaction data
# - BLACKLIST: Known high-risk entities
# - NEW_CUSTOMERS: Customers requiring risk assessment

# Load required tables
transactions = conn.table('TRANSACTIONS')
blacklist = conn.table('BLACKLIST')
new_customers = conn.table('NEW_CUSTOMERS')

# Create a graph from transactions
graph = ig.Graph(
    transactions,
    source_col='from_entity',
    target_col='to_entity',
)

# Get list of blacklisted entity IDs
blacklisted_ids = blacklist.select('entity_id').execute().entity_id.tolist()

# Calculate shortest paths from all blacklisted nodes
paths = graph.shortest_paths(sources=blacklisted_ids)

# Create risk scores based on distances
risk_assessment = (
    paths.select([
        paths.node_id,
        # Calculate minimum distance to any blacklisted entity
        paths.distances.min().name('min_distance_to_blacklist'),
        # Calculate average distance to blacklisted entities
        paths.distances.mean().name('avg_distance_to_blacklist'),
        # Count how many blacklisted entities are within 2 steps
        paths.distances.filter(lambda x: x <= 2).count().name('close_blacklist_count')
    ])
)

# Join with new customers to get their risk assessment
new_customer_risk = (
    new_customers
    .join(risk_assessment, new_customers.entity_id == risk_assessment.node_id)
    .select([
        'entity_id',
        'customer_name',
        'min_distance_to_blacklist',
        'avg_distance_to_blacklist',
        'close_blacklist_count'
    ])
)

# Execute the analysis
results = new_customer_risk.execute()
```

## Risk Scoring Framework

Here's how to interpret and use the distances for risk scoring:

```python
# Create a more sophisticated risk score
risk_scores = (
    new_customer_risk
    .mutate(
        risk_score=ibis.case()
            .when(risk_assessment.min_distance_to_blacklist <= 1, 1.0)  # Direct connection
            .when(risk_assessment.min_distance_to_blacklist == 2, 0.7)  # One intermediary
            .when(risk_assessment.min_distance_to_blacklist == 3, 0.4)  # Two intermediaries
            .when(risk_assessment.min_distance_to_blacklist == 4, 0.2)  # Three intermediaries
            .else_(0.1)                                                 # More distant
    )
)

# Add risk categories
categorized_risks = (
    risk_scores
    .mutate(
        risk_category=ibis.case()
            .when(risk_scores.risk_score >= 0.8, 'HIGH')
            .when(risk_scores.risk_score >= 0.5, 'MEDIUM')
            .else_('LOW')
    )
)
```

## Advanced Analysis Techniques

### Time-Based Analysis

Consider transaction recency in your analysis:

```python
# Create time-weighted graph
recent_transactions = transactions.filter(
    transactions.transaction_date >= '2024-01-01'
)

# Separate graphs for different time periods
recent_graph = ig.Graph(
    recent_transactions,
    source_col='from_entity',
    target_col='to_entity'
)

historical_graph = ig.Graph(
    transactions.filter(transactions.transaction_date < '2024-01-01'),
    source_col='from_entity',
    target_col='to_entity'
)

# Compare paths in different time periods
recent_paths = recent_graph.shortest_paths(blacklisted_ids)
historical_paths = historical_graph.shortest_paths(blacklisted_ids)
```

### Transaction Volume Consideration

Weight paths by transaction volumes:

```python
# Create graph with transaction amount weights
weighted_graph = ig.Graph(
    transactions,
    source_col='from_entity',
    target_col='to_entity',
    weight_col='transaction_amount'
)

# Higher weights mean stronger connections
weighted_paths = weighted_graph.shortest_paths(blacklisted_ids)
```

## Benefits of Using IbisGraph with Snowflake

1. **Data Security**
    - Sensitive transaction data never leaves Snowflake
    - Complies with data governance policies
    - Maintains audit trail within Snowflake

2. **Performance**
    - Leverages Snowflake's computational resources
    - Scales automatically with data volume
    - Efficient processing of large transaction networks

3. **Real-time Analysis**
    - Can be integrated into customer onboarding flows
    - Supports continuous monitoring
    - Easy to update as new transactions occur

4. **Compliance**
    - Maintains data lineage
    - Supports regulatory reporting requirements
    - Provides audit trails for risk decisions

## Practical Applications

1. **Customer Onboarding**
    - Pre-screen new customers
    - Set initial risk levels
    - Determine required due diligence level

2. **Ongoing Monitoring**
    - Track changes in risk proximity
    - Identify emerging risk patterns
    - Support suspicious activity reporting

3. **Portfolio Risk Management**
    - Assess aggregate exposure to high-risk entities
    - Monitor risk concentration
    - Support strategic decisions

This approach provides a data-driven, scalable solution for risk assessment while maintaining data security and leveraging existing infrastructure. It can be easily integrated into existing compliance workflows and supports both batch and real-time analysis needs.
