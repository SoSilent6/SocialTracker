from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def show_excel():
    # Read the CSV files
    x_sheet = pd.read_csv('X.csv')
    discord_sheet = pd.read_csv('Discord.csv')

    # Ensure the header row (row 1) is used to identify columns
    x_sheet.columns = x_sheet.columns.str.strip()
    discord_sheet.columns = discord_sheet.columns.str.strip()

    # Find "Token" and "Change" columns in the X and Discord sheets
    token_column_index_x = None
    change_column_index_discord = None

    for i, column in enumerate(x_sheet.columns):
        if "Token" in str(column):  # Match column header
            token_column_index_x = i
            break

    for i, column in enumerate(discord_sheet.columns):
        if "Change" in str(column):  # Match column header
            change_column_index_discord = i
            break

    if token_column_index_x is None:
        return "Error: 'Token' column not found in X sheet. Ensure the column header contains 'Token'."
    if token_column_index_x == 0:
        return "Error: 'Token' column is the first column in X sheet, so there is no column before it."
    if change_column_index_discord is None:
        return "Error: 'Change' column not found in Discord sheet."

    # Get the required columns
    token_column_name_x = x_sheet.columns[token_column_index_x]
    previous_column_name_x = x_sheet.columns[token_column_index_x - 1]
    discord_previous_column_name = discord_sheet.columns[token_column_index_x - 1]
    discord_change_column_name = discord_sheet.columns[change_column_index_discord]

    # Combine data into a new DataFrame for display
    result_df = pd.DataFrame({
        "Token": x_sheet[token_column_name_x],
        "X Followers": x_sheet[previous_column_name_x].fillna("No Data").apply(
            lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x
        ),
        "Change 24h (X)": x_sheet["Change"].apply(
            lambda x: "No Data" if pd.isna(x) else x  # Only replace NaN with "No Data"
        ),
        "Discord Followers": discord_sheet[discord_previous_column_name].fillna("No Data").apply(
            lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x
        ),
        "Change 24h (Discord)": discord_sheet[discord_change_column_name].apply(
            lambda x: "No Data" if pd.isna(x) else x  # Only replace NaN with "No Data"
        )
    })

    return render_template('index.html', data=result_df.to_html(index=False))

if __name__ == '__main__':
    app.run(debug=True)
