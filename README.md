## :hatched_chick: Polygon Data Viewer
This is an application to check financial data from [Polygon API](https://polygon.io) developed by Streamlit.<BR>
You can check news, companies informations, historical data, and earnings data.

### :rocket: Usage for Developers
The application is developed via devcontainer and docker, therefore you can develop it the same environment locally using .devcontainer/devcontainer.json.<BR>
Developers need setup API_KEY in secrets.toml under .streamlit directory like below.


```tree
your-LOCAL-repository/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml # Make sure to gitignore this!
├── your_app.py
└── requirements.txt
```

```toml, secrets.toml
API_KEY = "Y0UR_POLYGON_API_HERE"

[credentials]
[credentials.usernames.ADMIN]
name = "NAME_HERE"
password = "PASSWORD_HERE"
logged_in = false

[cookie]
name = "COOKIE_NAME_HERE"
key = "SECURITY_KEY_HERE"
expiry_days = 30

```

For more informations, read the [official documents](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management).

### :bulb: Tips
The application is fully depended on Polygon API.<BR>
IF the app shows error status 4XX or 5XX, PLEASE CHECK YOUR API KEY AND POLYGON API SERVER STATUS BELOW.

### :seedling: Polygon API Server Status
https://polygon.io/system
