from pathlib import Path
import sys

from langchain_core.tools import tool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.rag.retriever import search_documents


@tool
def search_parcelpilot_documents(
    query: str = "",
    q: str = "",
):
    """
    Search ParcelPilot's supplied policies, SOPs, customer agreements,
    and product documentation.

    Use this tool when the answer requires information from
    ParcelPilot documents.

    The search text can be supplied using either query or q.
    """

    # Accept either argument name.
    search_query = query.strip() if query else q.strip()

    if not search_query:
        return {
            "success": False,
            "message": "A search query is required."
        }

    results = search_documents(
        search_query,
        top_k=5
    )

    if not results:
        return {
            "success": False,
            "message": "No relevant information was found."
        }

    formatted_results = []

    for result in results:
        formatted_results.append({
            "source": result["source"],
            "page": result["page"],
            "relevance_score": round(
                result["score"],
                4
            ),
            "content": result["text"]
        })

    return {
        "success": True,
        "results": formatted_results
    }


if __name__ == "__main__":

    print("\n========== TESTING LLM DOCUMENT TOOL ==========\n")

    print("Available tool:")
    print("-", search_parcelpilot_documents.name)

    result = search_parcelpilot_documents.invoke({
        "query": "Can Northstar cancel a BOOKED shipment without a fee?"
    })

    for item in result["results"]:

        print("\n----------------------------------------")
        print(f"Source: {item['source']}")
        print(f"Page: {item['page']}")
        print(f"Score: {item['relevance_score']}")
        print(f"Content: {item['content'][:500]}")