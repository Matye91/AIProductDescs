import openai
import pandas as pd
import sqlite3
import os
import threading
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Global variables for logging progress
progress = {"completed": 0, "total": 0, "start_time": 0}
log_running = True

def progress_logger():
    """
    Logs progress and average speed to the terminal in a separate thread.
    """
    while log_running:
        elapsed_time = time.time() - progress["start_time"]
        average_speed = (progress["completed"] / elapsed_time) * 60 if elapsed_time > 0 else 0
        print(
            f"{progress['completed']} / {progress['total']} descriptions created "
            f"(aver. {average_speed:.2f} jobs/minute)", end="\r"
        )
        time.sleep(1)

def generate_description(product_name, short_desc, draft_desc):
    """
    Generate a comprehensive product description using OpenAI.
    Handles cases where short_desc or draft_desc are empty.
    """
    # Handle empty fields
    short_desc = short_desc if pd.notna(short_desc) and short_desc.strip() else "No short description available."
    draft_desc = draft_desc if pd.notna(draft_desc) and draft_desc.strip() else "No draft description available."

    # Create the prompt
    prompt = (
        f"Write a comprehensive, SEO-optimized product description for the following product:\n"
        f"Product Name: {product_name}\n"
        f"Short Description: {short_desc}\n"
        f"Draft Description: {draft_desc}\n"
        f"Ensure the product name is used as the main keyword. "
        f"Please use HTML tags (except h1) so I can easily insert it in my WooCommerce Astra theme webshop."
    )

    try:
        # Send the request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        # Extract and return the generated content
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error generating description for product '{product_name}': {e}")
        return None

def main():
    """
    Main function to process the CSV file and save results to a database.
    Handles errors and creates a separate file for remaining rows.
    """
    global log_running

    # Use a file dialog to select the input CSV file
    Tk().withdraw()  # Hide the root window
    input_file = askopenfilename(
        title="Select the input CSV file",
        filetypes=[("CSV files", "*.csv")]
    )

    if not input_file:
        print("No file selected. Exiting.")
        return

    # Read the semicolon-separated CSV file into a DataFrame
    try:
        df = pd.read_csv(input_file, sep=";")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Check if the required columns are present
    required_columns = ["Product Name", "Short Description", "Draft Description"]
    if not all(column in df.columns for column in required_columns):
        print(f"Input file must contain the following columns: {', '.join(required_columns)}")
        return

    # Initialize SQLite database
    db_file = os.path.splitext(input_file)[0] + ".db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create a table for storing descriptions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ProductDescriptions (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            short_description TEXT,
            draft_description TEXT,
            final_description TEXT
        )
    """)
    conn.commit()

    # Track progress
    progress["total"] = len(df)
    progress["completed"] = 0
    progress["start_time"] = time.time()

    # Start the progress logger thread
    log_thread = threading.Thread(target=progress_logger, daemon=True)
    log_thread.start()

    remaining_rows = []

    try:
        for _, row in df.iterrows():
            # Check if the product has already been processed
            cursor.execute("SELECT COUNT(*) FROM ProductDescriptions WHERE product_name = ?", (row["Product Name"],))
            if cursor.fetchone()[0] > 0:
                progress["completed"] += 1
                continue

            # Generate the description
            description = generate_description(row["Product Name"], row["Short Description"], row["Draft Description"])

            if description is not None:
                # Insert into database
                cursor.execute("""
                    INSERT INTO ProductDescriptions (product_name, short_description, draft_description, final_description)
                    VALUES (?, ?, ?, ?)
                """, (row["Product Name"], row["Short Description"], row["Draft Description"], description))
                conn.commit()
            else:
                # Save the row for retrying later
                remaining_rows.append(row)

            # Increment progress
            progress["completed"] += 1

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving progress...")

    finally:
        # Stop the progress logger
        log_running = False
        log_thread.join()

        # Save remaining rows to a CSV file
        if remaining_rows:
            remaining_file = os.path.splitext(input_file)[0] + "_remaining.csv"
            pd.DataFrame(remaining_rows).to_csv(remaining_file, sep=";", index=False)
            print(f"Remaining rows saved to: {remaining_file}")

        # Close the database connection
        conn.close()
        print(f"Database saved to: {db_file}")

if __name__ == "__main__":
    main()
