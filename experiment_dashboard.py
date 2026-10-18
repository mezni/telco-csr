def prepare_dashboard_data(experiments: list[dict]) -> list[dict]:
    """Convert saved experiments into dashboard-friendly rows."""
    rows = []

    for experiment in reversed(experiments):
        rows.append(
            {
                "Experiment": f"#{experiment['id']}",
                "Model": experiment["model"],
                "Category accuracy (%)": round(
                    experiment["category_accuracy"] * 100, 2
                ),
                "Order ID accuracy (%)": round(
                    experiment["order_id_accuracy"] * 100, 2
                ),
                "Lookup accuracy (%)": round(experiment["lookup_accuracy"] * 100, 2),
                "Overall accuracy (%)": round(
                    experiment["overall_field_accuracy"] * 100, 2
                ),
                "Average latency (ms)": round(experiment["average_latency_ms"], 2),
                "Input tokens": experiment["total_input_tokens"],
                "Output tokens": experiment["total_output_tokens"],
            }
        )

    return rows
