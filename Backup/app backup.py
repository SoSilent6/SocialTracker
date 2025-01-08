from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def show_excel():
   # Read both sheets from the single Excel file
   excel_file = pd.ExcelFile('Social Follower Count.xlsx')
   x_sheet = pd.read_excel(excel_file, 'X')
   discord_sheet = pd.read_excel(excel_file, 'Discord')
   
   x_sheet.columns = x_sheet.columns.str.strip()
   discord_sheet.columns = discord_sheet.columns.str.strip()

   def color_percentage(value):
       if isinstance(value, (str, float)) and value != "":
           try:
               # If it's a string, remove the % sign first
               val = float(str(value).replace('%', '')) if isinstance(value, str) else float(value)
               if val < 0:
                   return 'color: rgb(255, 68, 68)'  # Bright red
               elif val > 0:
                   return 'color: rgb(68, 255, 68)'  # Bright green
           except:
               pass
       return ''

   def format_token_column(value):
       return f'{value} <a href="/token/{value}" class="token-link">Details</a>'

   result_df = pd.DataFrame({
       "Token": x_sheet.iloc[:, 0],  # Column A (Token)
       "Change 24h (Vol)": x_sheet.iloc[:, 1].fillna(""),  # Column B (Change)
       "X Followers": x_sheet.iloc[:, 11].fillna("").apply(  # Column L (Followers)
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "Change 24h (X)": x_sheet.iloc[:, 1].fillna(""),  # Column B (Change) - same as Vol
       "Discord Followers": discord_sheet.iloc[:, 11].fillna("").apply(  # Column L (Followers)
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "Change 24h (Discord)": discord_sheet.iloc[:, 1].fillna(""),  # Column B (Change)
   })

   styled_df = result_df.style\
       .hide(axis='index')\
       .applymap(color_percentage, subset=['Change 24h (Vol)', 'Change 24h (X)', 'Change 24h (Discord)'])\
       .set_table_attributes('border="0" class="dataframe table table-dark table-striped" style="font-weight: normal"')\
       .set_table_styles([
           {'selector': 'th', 'props': [('font-weight', 'normal')]},
           {'selector': 'td', 'props': [('font-weight', 'normal')]}
       ])\
       .format({
           "Token": format_token_column,
           "X Followers": lambda x: "{:,}".format(x) if isinstance(x, (int, float)) else x,
           "Discord Followers": lambda x: "{:,}".format(x) if isinstance(x, (int, float)) else x,
           "Change 24h (Vol)": lambda x: f"{x}%" if x != "" else x,
           "Change 24h (X)": lambda x: f"{x}%" if x != "" else x,
           "Change 24h (Discord)": lambda x: f"{x}%" if x != "" else x
       })\
       .format_index(escape="html")

   html_table = styled_df.to_html()
   
   # Write to both locations - with explicit UTF-8 encoding
   with open("templates/index.html", "r", encoding='utf-8') as template_file:
       template_content = template_file.read()
   
   final_html = template_content.replace("{{ data | safe }}", html_table)
   
   # Write to root directory for Netlify - with explicit UTF-8 encoding
   with open("index.html", "w", encoding='utf-8') as f:
       f.write(final_html)
   
   # Return for Flask local development
   return render_template('index.html', data=html_table)

@app.route('/token/<token_name>')
def token_page(token_name):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{token_name} Details</title>
        <style>
            body {{
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }}
            
            .back-button {{
                color: #00ffcc;
                text-decoration: none;
                padding: 8px 16px;
                border: 1px solid #00ffcc;
                border-radius: 4px;
                margin: 20px;
                display: inline-block;
            }}
            
            .back-button:hover {{
                background: #00ffcc22;
            }}
        </style>
    </head>
    <body>
        <a href="/" class="back-button">← Back</a>
        <h1 style="color: #00ffcc;">{token_name}</h1>
        <p>Details coming soon...</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
   app.run(debug=True)