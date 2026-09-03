from app.connectors.jira.connector import JiraConnector


def main():
    connector = JiraConnector()

    items = connector.get_work_items("KAN")

    print()
    print("=" * 100)
    print("JIRA KAN WORK ITEMS")
    print("=" * 100)

    if not items:
        print("No work items found.")
        return

    for item in items:
        print(
            f"{item.id:8} | "
            f"{item.type:10} | "
            f"{item.delivery_role.value:15} | "
            f"parent={str(item.parent_id):10} | "
            f"SP={str(item.story_points):5} | "
            f"status={str(item.status):12} | "
            f"{item.title}"
        )

    print()
    print(f"TOTAL: {len(items)}")
    print("=" * 100)


if __name__ == "__main__":
    main()