import logging

logger = logging.getLogger(__name__)

def process_results(results, prefix, findings_list):
    """Helper to process search results into strings."""
    if isinstance(results, dict):
        actual_results = results.get("results", [])
        if isinstance(actual_results, list):
            for res in actual_results:
                if isinstance(res, dict):
                    content = res.get("content", str(res))
                    url = res.get("url", "No URL")
                    findings_list.append(f"[{prefix}] {content} (Source: {url})")
                else:
                    findings_list.append(f"[{prefix}] {res}")
        else:
            findings_list.append(f"[{prefix}] {results}")
    elif isinstance(results, list):
        for res in results:
            if isinstance(res, dict):
                content = res.get("content", str(res))
                url = res.get("url", "No URL")
                findings_list.append(f"[{prefix}] {content} (Source: {url})")
            elif isinstance(res, str):
                findings_list.append(f"[{prefix}] {res}")
            else:
                findings_list.append(f"[{prefix}] Received non-standard result type: {type(res)}")
    elif isinstance(results, str):
        findings_list.append(f"[{prefix}] {results}")
    else:
        logger.warning(f"Unexpected results format from {prefix}: {type(results)}")
