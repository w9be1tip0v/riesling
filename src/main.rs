use std::env;
use reqwest::Error;
use serde::Deserialize;
use serde_derive::Deserialize;

#[derive(Deserialize, Debug)]
struct Response {
    adjusted: bool,
    queryCount: i32,
    request_id: String,
    resultsCount: i32,
    status: String,
    ticker: String,
    results: Vec<ResultData>,
}

#[derive(Deserialize, Debug)]
struct ResultData {
    c: f64,  // close price
    h: f64,  // highest price
    l: f64,  // lowest price
    n: i32,  // number of transactions
    o: f64,  // open price
    t: i64,  // Unix Msec timestamp
    v: f64,  // trading volume
    vw: f64, // volume weighted average price
}

async fn fetch_historical_data(ticker: &str, from: &str, to: &str, api_key: &str) -> Result<Response, Error> {
    let url = format!(
        "https://api.polygon.io/v2/aggs/ticker/{}/range/1/day/{}/{}?apiKey={}",
        ticker, from, to, api_key
    );

    let response = reqwest::get(&url).await?.json().await?;

    Ok(response)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 4 {
        eprintln!("Usage: cargo run <ticker> <from> <to>");
        std::process::exit(1);
    }

    let ticker = &args[1];
    let from = &args[2];
    let to = &args[3];

    let api_key = match env::var("API_KEY") {
        Ok(key) => key,
        Err(_) => {
            eprintln!("Error: API_KEY environment variable not set");
            std::process::exit(1);
        }
    };

    let res = fetch_historical_data(ticker, from, to, &api_key).await?;

    println!("{:#?}", res);

    Ok(())
}
