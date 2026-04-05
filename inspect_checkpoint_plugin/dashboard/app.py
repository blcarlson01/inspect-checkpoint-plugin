import streamlit as st  # type: ignore[import-untyped]
from inspect_ai.log import list_eval_logs, read_eval_log

st.set_page_config(layout="wide")

def load_logs(path):
    logs = list_eval_logs(path)
    return sorted(logs, key=lambda x: x.mtime or 0.0, reverse=True)


def main():
    st.title("Inspect AI Live Checkpoints Dashboard")

    s3_path = st.text_input("S3 Path", "s3://my-bucket/run_123/checkpoints")

    logs = load_logs(s3_path)

    st.sidebar.write(f"{len(logs)} checkpoints found")

    if not logs:
        st.warning("No checkpoints found")
        return

    selected = st.selectbox(
        "Select checkpoint",
        logs,
        format_func=lambda x: x.name.split("/")[-1]
    )

    log = read_eval_log(selected.name)

    # Metrics
    st.header("Metrics")
    st.json(log.results)

    # Samples
    st.header("Samples")
    for sample in (log.samples or [])[:50]:
        st.write(sample)

    # Timeline
    st.header("Checkpoint Timeline")
    st.line_chart([
        len(read_eval_log(entry.name).samples or [])
        for entry in logs[::-1]
    ])


if __name__ == "__main__":
    main()