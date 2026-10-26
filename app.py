import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import plotly.express as px

def get_all_data(items,orders,users):
   df_items = pd.read_csv(items)
   df_orders = pd.read_csv(orders)
   df_users = pd.read_csv(users)
   merged1 = df_orders.merge(df_users, on='user_id', how='outer')
   merged2 = merged1.merge(df_items, on='item_id', how='outer')
   return merged2

def clean_data(indf):
   df = indf.copy()
   output_info = []
   df['price_per_unit'] = pd.to_numeric(df['price_per_unit'])
   df['quantity'] = pd.to_numeric(df['quantity'])
   df['order_date'] = pd.to_datetime(df['order_date'])
   df['base_price'] = pd.to_numeric(df['base_price'])
   df['registration_date'] = pd.to_datetime(df['registration_date'])

   na_sum = df[:].isnull().sum().sum()
   if na_sum > 0:
      cols_with_na = mis_col[mis_col > 0].index.tolist()
      if "order_id" in cols_with_na:
         output_info.append("Строки с пустыми заказами были удалены")
         df = df.dropna(subset=['order_id'])
      if "user_name" in cols_with_na:
         output_info.append("Неизвестные данные покупателей были заполнены как Unknown")
         df['user_name'] = df['user_name'].fillna("Unknown")
         df['city'] = df['city'].fillna("Unknown")
         df['user_segment'] = df['user_segment'].fillna("Unknown")
      if "item_name" in cols_with_na:
         output_info.append("Неизвестные категории были заполнены как Unknown")
         df['item_name'] = df['item_name'].fillna("Unknown")
         df['category'] = df['category'].fillna("Unknown")
         df['supplier'] = df['supplier'].fillna("Unknown")
   else:
      output_info.append("Все поля датафрейма заполнены и не потребовали импутации")

   return df, output_info

st.set_page_config(
   page_title = "Дашборд анализа продаж",
   layout = "wide"
)

tab1, tab2 = st.tabs(["Исходные данные и метрики по фильтрам", "Визуализация и анализ исходных данных"])

with tab1:
   st.subheader("Исходные данные")

   st.html(
      """
      <style>
      [data-testid="stSidebarContent"] {
        color: black;
        background-color: lavender;
      } 
   </style>
   """
   )

   df_init = get_all_data("items.csv","orders.csv","users.csv")
   df, info_clean  = clean_data(df_init)

   for line in info_clean:
      st.markdown(f'<p style="background-color:#B8D4F1;color:black;font-size:18px;border-radius:6%;">{line}</p>', unsafe_allow_html=True)

   st.dataframe(df)

   with st.sidebar:
      st.header("Фильтры")
      list_cat = ["Любая"] + list(sorted(df["category"].unique()))
      selected_cat = st.selectbox("Выберите Категорию", options = list_cat)

      date_min = df['order_date'].min().date()
      date_max = df['order_date'].max().date()
      date_range = st.sidebar.date_input(
         "Выберите даты:",
         value=(date_min, date_max),
         min_value=date_min,
         max_value=date_max,
         format="YYYY-MM-DD"
      )

   if selected_cat != "Любая":
      filtered_df = df[df["category"] == selected_cat]
   else:
      filtered_df = df.copy()

   st.subheader("Результаты фильтрации:")

   try:
      start_date, end_date = date_range
      filtered_df = filtered_df[
         (filtered_df["order_date"].dt.date >= start_date)
         & (filtered_df["order_date"].dt.date <= end_date)
      ]
      st.dataframe(filtered_df)
   except Exception:
      st.error("В выбранной категории нет таких дат")

   st.subheader("Ключевые показатели  по категории и датам:")

   num_orders = len(filtered_df)
   revenue = (filtered_df['quantity']*filtered_df['price_per_unit']).sum()
   num_users = filtered_df['user_id'].nunique()

   def custom_metric(label, value, bg_color):
      html_code = f"""
       <div style="
        background-color: {bg_color};
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        font-family: sans-serif;
        margin-bottom: 10px;
       ">
        <p style="margin: 0; font-size: 14px; color: #555;">{label}</p>
        <p style="margin: 5px 0; font-size: 28px; font-weight: bold; color: #111;">{value}</p>
       </div>
       """
      return st.html(html_code)

   m1, m2 = st.columns(2)

   with m1:
      custom_metric("Количество заказов", num_orders, "#FFEBEE")
   with m2:
      custom_metric("Общая выручка", revenue, "#E8F5E9")

   m3, m4 = st.columns(2)

   with m3:
      custom_metric("Количество пользователей", num_users, "#E3F2FD")
   with m4:
      custom_metric("Средний чек", f"{revenue/num_orders:.2f}", "#FFF3E0")

with tab2:
   df2 = df.copy()
   df2["revenue"] = df2['quantity']*df2['price_per_unit']
   top_10_products = (
      df2.groupby('item_name')['revenue']
      .sum()
      .reset_index()
      .sort_values(by='revenue', ascending=False)
      .head(10)
   )

   st.subheader("Топ-10 товаров по выручке")

   fig, ax = plt.subplots(figsize=(8, 5))

   ax.barh(top_10_products["item_name"],
         top_10_products["revenue"],
         color="skyblue",
         edgecolor="black")

   ax.set_xlabel("Выручка", fontsize=12)
   ax.set_ylabel("Товары", fontsize=12)
   ax.spines['top'].set_visible(False)
   ax.spines['right'].set_visible(False)

   ax.xaxis.grid(True, linestyle='--', alpha=0.6)
   ax.set_axisbelow(True)

   st.pyplot(fig)

   st.subheader("Распределение выручки по категориям товаров")
   fig2 = px.pie(
      df2,
      values="revenue",
      names="category",
      color_discrete_sequence=px.colors.sequential.RdBu
   )

   fig2.update_traces(
      textposition="inside",
      textinfo="percent+label",
      hovertemplate="<b>%{label}</b><br>Выручка: %{value:,.0f}<br>Доля: %{percent}"
   )

   st.plotly_chart(fig2, use_container_width=True)

   st.subheader("Зависимость количества заказов от дня недели")

   df2['dt'] = pd.to_datetime(df2['order_date'])
   df2['week_day'] = df2['dt'].dt.dayofweek

   df_weekday_orders = (
      df2.groupby('week_day')['order_id']
      .count()
      .reset_index()
      .sort_values(by='order_id', ascending=True)
   )

   fig3 = px.bar(
      df_weekday_orders,
      x='week_day',
      y='order_id',
      color= 'order_id',
      color_continuous_scale = "bupu",
      labels={
         "week_day": "Дни недели",
         "order_id": "Количество заказов"
      },
      text_auto=True
   )

   fig3.update_traces(
      marker_line_color='black', # Цвет границ столбцов
      marker_line_width=1.5      # Толщина границ
   )
   fig3.update_xaxes(
      tickvals=[0, 1, 2, 3, 4, 5, 6],
      ticktext=['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Субота', 'Воскресенье']
   )

# Настройка осей, шрифтов и легенды
   fig3.update_layout(
      xaxis_title_font=dict(size=14, family='Arial', color='darkblue'),
      yaxis_title_font=dict(size=14, family='Arial', color='darkblue'),
      coloraxis_showscale=False,
      yaxis=dict(showgrid=True, gridcolor='LightGray'), # Включаем сетку
      margin=dict(l=40, r=40, t=60, b=40), # Отступы от краев
      height=500 # Высота графика в пикселях
)

   st.plotly_chart(fig3, use_container_width=True)

   st.subheader("Аналитические выводы")

   cat_max = df2.groupby('category')['revenue'].sum()

   max_category = cat_max.idxmax()
   max_revenue = cat_max.max()

   st.markdown(
      f"Основная выручка приходится на категорию <span style='color:red; font-weight:bold;'>{max_category} ( Выручка составила {max_revenue})</span>",
      unsafe_allow_html=True
   )

   max_val_for_week = df_weekday_orders['order_id'].max()
   days_week = df_weekday_orders[df_weekday_orders['order_id'] == max_val_for_week]
   days_ru = {
      0: 'Понедельник', 1: 'Вторник', 2: 'Среда',
      3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
   }

   days_week['day_name'] = df_weekday_orders['week_day'].map(days_ru)
   list_days =  ", ".join(days_week['day_name'])

   st.markdown(
      f"Дни недели с максимальным количеством заказов: <span style='color:red; font-weight:bold;'>{list_days}</span>",
      unsafe_allow_html=True
   )

   st.markdown(
      f"Товар <span style='color:red; font-weight:bold;'>{top_10_products.iloc[0]['item_name']}</span> является лидером продаж",
      unsafe_allow_html=True
   )