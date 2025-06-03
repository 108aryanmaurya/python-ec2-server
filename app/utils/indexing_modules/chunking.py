from .topic_extraction import extract_topics_gpt
def chunking(segments, metadata, target_secs=20, overlap_secs=5, n_topics=5):
    """
    Chunks a list of segments (with start, end, text) into new chunks based on duration.
    Each chunk has up to target_secs seconds, with overlap_secs overlap between chunks.
    Adds a list of topics for each chunk.
    Returns: List of new chunks, each with combined text, recalculated timestamps, and topics.
    """
    chunks = []
    current_chunk = []
    chunk_start = None
    chunk_end = None
    last_end = 0
    chunk_id = 0

    i = 0
    n = len(segments)
    while i < n:
        if not current_chunk:
            # Start new chunk
            chunk_start = segments[i].start
            chunk_end = chunk_start + target_secs
        seg = segments[i]
        # If segment fits in chunk, add it
        if seg.start < chunk_end:
            current_chunk.append(seg)
            last_end = seg.end
            i += 1
        else:
            # Save current chunk
            text = " ".join(s.text.strip() for s in current_chunk)
            topics = extract_topics_gpt(text, n_topics=n_topics)
            chunk = {
                "chunk_id": chunk_id,
                "text": text,
                "start_time": chunk_start,
                "end_time": last_end,
                "topics": topics,
            }
            chunk.update(metadata)
            chunks.append(chunk)
            chunk_id += 1
            # Start next chunk with overlap
            overlap_start = chunk_end - overlap_secs
            j = i
            while j > 0 and segments[j-1].start >= overlap_start:
                j -= 1
            i = j
            current_chunk = []

    # Add any remaining chunk
    if current_chunk:
        text = " ".join(s.text.strip() for s in current_chunk)
        topics = extract_topics_gpt(text, n_topics=n_topics)
        print("TOPICS-----------------------------")
        print("TOPICS-----------------------------")
        chunk = {
            "chunk_id": chunk_id,
            "text": text,
            "start_time": chunk_start,
            "end_time": last_end,
            "topics": topics,
        }
        chunk.update(metadata)
        chunks.append(chunk)

    return chunks
