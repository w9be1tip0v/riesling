import streamlit as st

# Apply default sort and display the data
def display_data_with_default_sort(df, sort_column):
    if not df.empty:
        df_sorted = df.sort_values(by=sort_column, ascending=False)
        st.dataframe(df_sorted)
    else:
        st.error("No data found.")

# Escape Markdown special characters
def escape_markdown(text):
    # Special characters in Markdown
    markdown_special_chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|", ":", "$", ">"]
    for char in markdown_special_chars:
        text = text.replace(char, f"\\{char}")
    
    return text