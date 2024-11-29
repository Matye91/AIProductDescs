# OpenAI Product Description Generator

This project generates SEO-optimized product descriptions using the OpenAI API. It processes product data from a CSV file, interacts with the OpenAI API to generate descriptions, and stores the results in an SQLite database. The project includes error handling for failed API requests, logs progress in real-time, and outputs any remaining unprocessed rows for further retries.

## Features

- **Uses OpenAI API (e.g., GPT-4o-mini)** to generate product descriptions.
- **Handles large datasets** with progress logging and average speed metrics (jobs/minute).
- **Saves results in an SQLite database** for reliability and faster processing.
- **Handles API errors gracefully**, saving unprocessed rows to a separate CSV file for retries.
- **Secure API key management** via system environment variables.

---

## Requirements

- Python 3.8 or later
- Required Python libraries:
  - `openai`
  - `pandas`
  - `sqlite3` (built into Python)
  - `tkinter` (built into Python)

Install required libraries using pip:

```bash
pip install openai pandas

```

## Input File Requirements

The input file must be a semicolon-separated CSV file with the following headers:

Product Name (required): The name of the product.
Short Description (optional): A brief description of the product.
Draft Description (optional): A longer draft description of the product.
Example:
Product Name;Short Description;Draft Description
Eco Water Bottle;Reusable bottle;Made from sustainable materials.
Garden Rake;;Lightweight rake for gardening.
Lawn Mower;;

## Output Files

### SQLite Database:

The output is stored in an SQLite database file (.db) located in the same directory as the input file. The database contains the following table:

ProductDescriptions Table:
Column Description
id Row ID (Primary Key)
product_name Product name (from input)
short_description Short description (from input)
draft_description Draft description (from input)
final_description SEO-optimized product description (generated)

### Remaining Rows CSV:

If the API fails for certain rows (e.g., due to connection issues), they will be saved in a CSV file named inputfile_remaining.csv.

Example Remaining File:
Product Name;Short Description;Draft Description
Garden Rake;;Lightweight rake for gardening.
Lawn Mower;;
