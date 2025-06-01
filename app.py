import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import time

# CSS
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stApp { background-color: #f8fafc; }
        h1, h2 {
            color: #1a202c;
            font-family: 'Segoe UI',sans-serif;
        }
        .stDataFrame {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 24px 0 rgba(0,0,0,0.04);
        }
        .css-1v0mbdj {background: #f8fafc;}
        .sidebar .sidebar-content {background: #e2e8f0;}
    </style>
""", unsafe_allow_html=True)

ratings = pd.read_csv("ratings.csv")
movies = pd.read_csv("movies.csv")

def extract_year(title):
    import re
    match = re.search(r'\((\d{4})\)', title)
    return int(match.group(1)) if match else None

movies["year"] = movies["title"].apply(extract_year)
movies["genres_list"] = movies["genres"].apply(lambda x: x.split('|'))
data = pd.merge(ratings, movies, on="movieId")

st.sidebar.title("🎬 Navigacija")
page = st.sidebar.radio("Izberi stran", ["Top 10 filmov", "Primerjava filmov", "Priporočila"])

if page == "Top 10 filmov":
    min_ratings = st.sidebar.slider("📊 Minimalno število ocen", 1, 100, 10)
    all_genres = sorted(set(g for genres in movies['genres_list'] for g in genres if g != '(no genres listed)'))
    genre = st.sidebar.selectbox("🎞️ Izberi žanr", ["Vsi"] + all_genres)
    year_options = sorted([y for y in movies['year'].dropna().unique() if y is not None])
    year = st.sidebar.selectbox("📅 Izberi leto", ["Vsa leta"] + [int(y) for y in year_options])

    filtered = data.copy()
    if genre != "Vsi":
        filtered = filtered[filtered['genres_list'].apply(lambda genres: genre in genres)]
    if year != "Vsa leta":
        filtered = filtered[filtered['year'] == int(year)]

    agg = filtered.groupby(['movieId', 'title']).agg(
        povprecna_ocena = ('rating', 'mean'),
        stevilo_ocen = ('rating', 'count')
    ).reset_index()

    agg = agg[agg['stevilo_ocen'] >= min_ratings]
    top10 = agg.sort_values("povprecna_ocena", ascending=False).head(10)
    top10['povprecna_ocena'] = top10['povprecna_ocena'].round(2)
    top10 = top10.reset_index(drop=True)
    top10.insert(0, 'Mesto', range(1, len(top10) + 1))
    top10 = top10.rename(columns={
        'title': 'Naslov',
        'povprecna_ocena': 'Povprečna ocena',
        'stevilo_ocen': 'Število ocen'
    })

    st.markdown("# ⭐ Top 10 filmov po povprečni oceni")
    st.markdown("#### Interaktivni pregled najboljših filmov v zbirki MovieLens")
    st.write(
        "Uporabi filtre levo, da izbereš žanr, leto ali minimalno število ocen.\n"
        "Seznam prikazuje filme, ki so prejeli največje povprečne ocene od uporabnikov."
    )
    st.markdown(
        f"**Aktivni filtri:** "
        f"<span style='color:#6366f1'>{min_ratings}+ ocen</span>, "
        f"<span style='color:#6366f1'>{genre}</span>, "
        f"<span style='color:#6366f1'>{year}</span>",
        unsafe_allow_html=True
    )
    st.dataframe(
        top10[["Mesto", "Naslov", "Povprečna ocena", "Število ocen"]],
        use_container_width=True,
        hide_index=True
    )

elif page == "Primerjava filmov":
    st.markdown("# 🎥 Primerjava dveh filmov")
    st.write("Izberi dva filma za podrobno primerjavo ocen:")

    movie_options = movies.sort_values('title')['title'].tolist()
    film1 = st.selectbox("Izberi prvi film", movie_options, key='film1')
    film2 = st.selectbox("Izberi drugi film", movie_options, index=1, key='film2')

    id1 = movies.loc[movies['title'] == film1, 'movieId'].values[0]
    id2 = movies.loc[movies['title'] == film2, 'movieId'].values[0]

    r1 = ratings[ratings['movieId'] == id1]['rating']
    r2 = ratings[ratings['movieId'] == id2]['rating']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📽️ {film1}")
        st.write(f"Povprečna ocena: **{r1.mean():.2f}**")
        st.write(f"Število ocen: **{r1.count()}**")
        st.write(f"Standardni odklon: **{r1.std():.2f}**")
    with col2:
        st.subheader(f"📽️ {film2}")
        st.write(f"Povprečna ocena: **{r2.mean():.2f}**")
        st.write(f"Število ocen: **{r2.count()}**")
        st.write(f"Standardni odklon: **{r2.std():.2f}**")

    st.markdown("### Histogram ocen")
    fig, ax = plt.subplots()
    ax.hist(r1, bins=[0.5,1.5,2.5,3.5,4.5,5.5], alpha=0.6, label=film1, color='tab:blue')
    ax.hist(r2, bins=[0.5,1.5,2.5,3.5,4.5,5.5], alpha=0.6, label=film2, color='tab:orange')
    ax.set_xlabel("Ocena")
    ax.set_ylabel("Število")
    ax.legend()
    st.pyplot(fig)

    st.markdown("### Povprečna letna ocena")
    ratings["year"] = pd.to_datetime(ratings["timestamp"], unit='s').dt.year
    avg_year1 = ratings[ratings['movieId'] == id1].groupby('year')['rating'].mean()
    avg_year2 = ratings[ratings['movieId'] == id2].groupby('year')['rating'].mean()
    fig2, ax2 = plt.subplots()
    ax2.plot(avg_year1.index, avg_year1.values, marker='o', label=film1)
    ax2.plot(avg_year2.index, avg_year2.values, marker='o', label=film2)
    ax2.set_xlabel("Leto")
    ax2.set_ylabel("Povprečna ocena")
    ax2.legend()
    st.pyplot(fig2)

    st.markdown("### Število ocen na leto")
    count_year1 = ratings[ratings['movieId'] == id1].groupby('year')['rating'].count()
    count_year2 = ratings[ratings['movieId'] == id2].groupby('year')['rating'].count()
    all_years = sorted(set(count_year1.index).union(set(count_year2.index)))
    counts1 = [count_year1.get(y, 0) for y in all_years]
    counts2 = [count_year2.get(y, 0) for y in all_years]
    width = 0.4
    x = np.arange(len(all_years))
    fig3, ax3 = plt.subplots()
    ax3.bar(x - width/2, counts1, width=width, label=film1, color='tab:blue')
    ax3.bar(x + width/2, counts2, width=width, label=film2, color='tab:orange')
    ax3.set_xlabel("Leto")
    ax3.set_ylabel("Število ocen")
    ax3.set_xticks(x)
    ax3.set_xticklabels(all_years, rotation=45)
    ax3.legend()
    st.pyplot(fig3)

elif page == "Priporočila":
    st.markdown("# 🍿 Priporočilni sistem")
    st.write("Registriraj se ali prijavi in začni ocenjevati filme. Po 10 ocenah dobiš priporočila.")

    users_file = "users.csv"
    ratings_file = "user_ratings.csv"

    if not os.path.exists(users_file):
        pd.DataFrame(columns=["username", "password"]).to_csv(users_file, index=False)
    if not os.path.exists(ratings_file):
        pd.DataFrame(columns=["username", "movieId", "rating", "timestamp"]).to_csv(ratings_file, index=False)

    def check_login(username, password):
        users = pd.read_csv(users_file)
        return ((users["username"] == username) & (users["password"] == password)).any()

    def register_user(username, password):
        users = pd.read_csv(users_file)
        if username in users["username"].values:
            return False
        new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
        users = pd.concat([users, new_user], ignore_index=True)
        users.to_csv(users_file, index=False)
        return True

    def save_user_rating(username, movieId, rating):
        df = pd.read_csv(ratings_file)
        timestamp = int(time.time())
        new_rating = pd.DataFrame([[username, movieId, rating, timestamp]], columns=["username", "movieId", "rating", "timestamp"])
        df = pd.concat([df, new_rating], ignore_index=True)
        df.to_csv(ratings_file, index=False)

    def user_rated_movies(username):
        df = pd.read_csv(ratings_file)
        return df[df["username"] == username]

    session_key = "prijavljen_uporabnik"

    if session_key not in st.session_state:
        st.markdown("#### Nisi prijavljen/a? Prijavi se ali ustvari nov račun:")
        tabs = st.tabs(["Prijava", "Registracija"])
        with tabs[0]:
            uname = st.text_input("Uporabniško ime", key="login_user")
            pwd = st.text_input("Geslo", type="password", key="login_pass")
            login_btn = st.button("Prijava")
            if login_btn:
                if check_login(uname, pwd):
                    st.session_state[session_key] = uname
                    st.success(f"Prijava uspešna! Pozdravljen, {uname}!")
                    st.rerun()  # Takoj rerun po prijavi
                else:
                    st.error("Napačno uporabniško ime ali geslo.")
        with tabs[1]:
            uname_r = st.text_input("Uporabniško ime", key="reg_user")
            pwd_r = st.text_input("Geslo", type="password", key="reg_pass")
            reg_btn = st.button("Registracija")
            if reg_btn:
                if register_user(uname_r, pwd_r):
                    st.success("Registracija uspešna! Sedaj se lahko prijaviš.")
                else:
                    st.error("Uporabniško ime že obstaja.")

    else:
        current_user = st.session_state[session_key]
        st.info(f"Prijavljeni ste kot: **{current_user}**")
        if st.button("Odjava"):
            del st.session_state[session_key]
            st.rerun()
        st.write("---")

        user_movies = user_rated_movies(current_user)
        rated_movie_ids = user_movies["movieId"].astype(int).tolist()
        unrated_movies = movies[~movies["movieId"].isin(rated_movie_ids)]

        st.subheader("Ocenjevanje filmov")
        film_izbira = st.selectbox("Izberi film za ocenjevanje", unrated_movies["title"].tolist())
        ocena = st.slider("Tvoja ocena (1-5)", 1, 5, 3)
        if st.button("Oddaj oceno"):
            film_id = movies[movies["title"] == film_izbira]["movieId"].values[0]
            save_user_rating(current_user, film_id, ocena)
            st.success("Ocena uspešno shranjena! Osveži stran za nove možnosti.")

        user_movies = user_rated_movies(current_user)
        st.write(f"Do zdaj si ocenil/a **{len(user_movies)}** filmov.")

        if len(user_movies) >= 10:
            st.subheader("🎯 Priporočeni filmi zate")
            user_with_genres = user_movies.merge(movies, on="movieId")
            genre_ratings = user_with_genres.explode("genres_list").groupby("genres_list")["rating"].mean()
            if len(genre_ratings) == 0:
                st.info("Za priporočila najprej oceni nekaj filmov.")
            else:
                favorite_genre = genre_ratings.sort_values(ascending=False).index[0]
                priporocila = movies[
                    (movies["genres_list"].apply(lambda gl: favorite_genre in gl)) &
                    (~movies["movieId"].isin(rated_movie_ids))
                ].copy()
                priporocila = priporocila.merge(ratings.groupby("movieId")["rating"].mean(), on="movieId", how="left")
                priporocila = priporocila.rename(columns={"rating": "Povprečna ocena"})
                priporocila = priporocila.sort_values("Povprečna ocena", ascending=False).head(10)

                st.write(f"Tvoj najljubši žanr je **{favorite_genre}**.")
                st.dataframe(
                    priporocila[["title", "genres", "Povprečna ocena"]]
                    .rename(columns={"title": "Naslov", "genres": "Žanri"})
                    .reset_index(drop=True),
                    use_container_width=True
                )
        else:
            st.warning("Za priporočila moraš najprej oceniti vsaj 10 filmov.")