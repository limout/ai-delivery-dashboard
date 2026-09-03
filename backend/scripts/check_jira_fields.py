from app.connectors.jira.connector import JiraConnector


def main():
    connector = JiraConnector()

    response = connector.session.get(
        f"{connector.base_url}/rest/api/3/field",
        timeout=30,
    )

    response.raise_for_status()

    fields = response.json()

    print("=" * 100)
    print("JIRA CUSTOM FIELDS")
    print("=" * 100)

    for field in fields:
        field_id = field.get("id", "")
        name = field.get("name", "")
        schema = field.get("schema") or {}

        # Показываем только custom fields.
        if field_id.startswith("customfield_"):
            print(
                f"{field_id:25} | "
                f"{name:40} | "
                f"type={schema.get('type')} | "
                f"custom={schema.get('custom')}"
            )

    print("=" * 100)


if __name__ == "__main__":
    main()