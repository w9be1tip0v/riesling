## Polygon Data Viewer
This is an application to check US Equity data from [Polygon API](https://polygon.io).<BR>
You can check news, companies informations, historical data, and earnings data.

## Usage for Developers
The application is developed via devcontainer and docker, therefore you can develop it the same environment locally using .devcontainer/devcontainer.json.<BR>
Developers need setup the .env file like below.

```UNIX, .env
API_KEY=Y0UR_POLYGON_API_HERE
```

### Streamlit app developers
The environment file is needed placed in .streamlit/secret.toml like below.

```tree
your-LOCAL-repository/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml # Make sure to gitignore this!
├── your_app.py
└── requirements.txt
```

For more informations, read the [official documents](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management).

# Tips
The application is fully depended on Polygon API.<BR>
IF the app shows error status 4XX or 5XX, PLEASE CHECK YOUR API KEY AND POLYGON API SERVER STATUS BELOW.

### Polygon API Server Status
https://polygon.io/system
