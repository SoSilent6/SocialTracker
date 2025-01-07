from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def show_excel():
   x_sheet = pd.read_csv('X.csv')
   discord_sheet = pd.read_csv('Discord.csv')
   
   x_sheet.columns = x_sheet.columns.str.strip()
   discord_sheet.columns = discord_sheet.columns.str.strip()

   token_column_index_x = next((i for i, col in enumerate(x_sheet.columns) if "Token" in str(col)), None)
   change_column_index_discord = next((i for i, col in enumerate(discord_sheet.columns) if "Change" in str(col)), None)
   change_3d_column_x = next((i for i, col in enumerate(x_sheet.columns) if "3D" in str(col)), None)
   change_3d_column_discord = next((i for i, col in enumerate(discord_sheet.columns) if "3D" in str(col)), None)

   if not all([token_column_index_x, token_column_index_x > 0, change_column_index_discord, change_3d_column_x, change_3d_column_discord]):
       return "Error: Required columns not found"

   def color_percentage(value):
       if isinstance(value, str):
           try:
               val = float(value.strip('%'))
               if val < 0:
                   return 'color: #ff4444'
               elif val > 0:
                   return 'color: #44ff44'
           except:
               pass
       return ''

   result_df = pd.DataFrame({
       "Token": x_sheet.iloc[:, token_column_index_x],
       "X Followers": x_sheet.iloc[:, token_column_index_x - 1].fillna("No Data").apply(
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "Change 24h (X)": x_sheet["Change"].fillna("No Data"),
       "Change 3D (X)": x_sheet.iloc[:, change_3d_column_x].fillna("No Data"),
       "Discord Followers": discord_sheet.iloc[:, token_column_index_x - 1].fillna("No Data").apply(
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "Change 24h (Discord)": discord_sheet.iloc[:, change_column_index_discord].fillna("No Data"),
       "Change 3D (Discord)": discord_sheet.iloc[:, change_3d_column_discord].fillna("No Data")
   })

   styled_df = result_df.style\
       .hide(axis='index')\
       .applymap(color_percentage, subset=['Change 24h (X)', 'Change 3D (X)', 'Change 24h (Discord)', 'Change 3D (Discord)'])\
       .set_table_attributes('border="0" class="dataframe"')\
       .format({
           "Change 24h (X)": lambda x: x if x == "No Data" else x,
           "Change 3D (X)": lambda x: x if x == "No Data" else x,
           "Change 24h (Discord)": lambda x: x if x == "No Data" else x,
           "Change 3D (Discord)": lambda x: x if x == "No Data" else x
       })

   html_table = styled_df.to_html()
   
   # Write to both locations
   with open("templates/index.html", "r") as template_file:
       template_content = template_file.read()
   
   final_html = template_content.replace("{{ data | safe }}", html_table)
   
   # Write to root directory for Netlify
   with open("index.html", "w") as f:
       f.write(final_html)
   
   # Return for Flask local development
   return render_template('index.html', data=html_table)

if __name__ == '__main__':
   app.run(debug=True)