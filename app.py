from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from car_part_scraper import run_scraper  # your existing process(year, model, part, country) function

app = FastAPI()

class ScrapeParams(BaseModel):
    year: str
    model: str
    part: str
    country: str

@app.post("/scrape")
def scrape(params: ScrapeParams):
    return run_scraper(params.year, params.model, params.part, params.country)
