"""
review_explorer.py — the Streamlit page: filter the mentions, and ask the reviews.

Run it from the repository root with:  streamlit run code/review_explorer.py
"""

import os

import streamlit as st

import reviews
from reviews.aspects import (
    analyze_reviews,
    answer_question,
    build_messages,
    describe_scope,
    load_aliases,
    summarize_items,
)
from reviews.settings import REVIEWS_FILE

reviews_file = os.environ.get("REVIEWS_FILE", REVIEWS_FILE)

mentions = analyze_reviews(reviews_file)
aliases = load_aliases()

st.title("Salt City Coffee — What Customers Are Saying")

locations = ["All"] + sorted(mentions["location"].unique())
subjects = ["All"] + sorted(mentions["subject"].unique())
left, right = st.columns(2)
location = left.selectbox("Location", locations, key="location")
subject = right.selectbox("Subject", subjects, key="subject")

filtered = mentions
if location != "All":
    filtered = filtered[filtered["location"] == location]
if subject != "All":
    filtered = filtered[filtered["subject"] == subject]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Reviews", filtered["review_id"].nunique())
col2.metric("Mentions", len(filtered))
col3.metric("Positive", int((filtered["mention_sentiment"] == "positive").sum()))
col4.metric("Negative", int((filtered["mention_sentiment"] == "negative").sum()))

summary = summarize_items(filtered)
praised = summary[summary["net"] > 0].sort_values(
    ["net", "mentions"], ascending=[False, False]).head(5)
complained = summary[summary["net"] < 0].sort_values(
    ["net", "mentions"], ascending=[True, False]).head(5)

praised_tab, complained_tab, said_tab = st.tabs(
    ["Most praised", "Most complained about", "What people said"])
with praised_tab:
    st.dataframe(praised, hide_index=True)
with complained_tab:
    st.dataframe(complained, hide_index=True)
with said_tab:
    st.dataframe(filtered, hide_index=True)

st.subheader("Ask the reviews")
question = st.text_input("Your question", key="question",
                         placeholder="Do people like the mocha latte?")

if st.button("Ask", key="ask") and question.strip():
    scope, evidence = answer_question(question, mentions, aliases)
    if evidence.empty:
        st.warning(f"No review mentions {describe_scope(scope)}, "
                   "so there is nothing to answer from.")
    else:
        with st.spinner("Reading the reviews..."):
            answer = reviews.ask_llm(build_messages(question, evidence))
        st.write(answer)
        st.caption(f"Based on {len(evidence)} mentions: {describe_scope(scope)}")
        st.dataframe(evidence, hide_index=True)
