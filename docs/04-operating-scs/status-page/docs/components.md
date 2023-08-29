# Components

Illustrating multiple interchangable logical "layers" of possible Status Page application stacks:

```mermaid
  C4Container
  title SCS Status Page components
  UpdateLayoutConfig("100", "1")
  Boundary(b4, "Application layer") {
    Container(app1, "Flask App", "OAuth2 impl. etc.")
    Container(app2, "Vue App", "OAuth2 impl. etc.")
    Container(app3, "CLI Client", "CLI Client")
  }
  Boundary(b3, "Policy layer") {
    Container(policy1, "istio end-user auth", "")
    Container(policy2, "custom auth proxy", "")
    Container(policy3, "Caddy", "")
  }
  Boundary(b2, "API server layer") {
    Container(api1, "API Server (Go)", "")
    Container(api2, "API Server (Python)", "")
    Container(api3, "API Server (Go)", "")
  }
  Boundary(b1, "Database layer") {
    Container(db1, "postgres", "")
    Container(db2, "mysql", "")
    Container(db3, "github", "Github Projects API")
  }
  Rel(api1, db1, "Uses", "Postgres protocol")
  Rel(api2, db2, "Uses", "MySQL protocol")
  Rel(api3, db3, "Uses", "GraphQL API")
  Rel(policy1, api1, "Relays", "SCS Status Page API")
  Rel(policy2, api2, "Relays", "SCS Status Page API")
  Rel(policy3, api3, "Relays", "SCS Status Page API")
  Rel(app1, policy1, "Requests", "SCS Status Page API + Auth")
  Rel(app2, policy2, "Requests", "SCS Status Page API + Auth")
  Rel(app3, policy3, "Requests", "SCS Status Page API + Auth")
```

Note that not everything that is shown here, actually exists or was tested. It is just shown for illustration purposes.
