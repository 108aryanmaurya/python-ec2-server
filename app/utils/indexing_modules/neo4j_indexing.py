from neo4j import GraphDatabase

neo4j_driver = GraphDatabase.driver(
    "bolt://neo4j:7687", auth=("neo4j", "password123")
)

def index_chunks_in_neo4j(course_info, section_info, lesson_info, video_info, chunks):
    with neo4j_driver.session() as session:
        # Course node
        session.run("""
            MERGE (c:Course {id: $course_id, name: $course_name})
            """, course_id=course_info.course_id, course_name=course_info.course_name)
        
        # Section node
        session.run("""
            MATCH (c:Course {id: $course_id})
            MERGE (s:Section {id: $section_id, name: $section_name})
            MERGE (c)-[:HAS_SECTION]->(s)
            """, course_id=course_info.course_id, section_id=section_info.section_id, section_name=section_info.section_name)
        
        # Lesson node
        session.run("""
            MATCH (s:Section {id: $section_id})
            MERGE (l:Lesson {id: $lesson_id, name: $lesson_name})
            MERGE (s)-[:HAS_LESSON]->(l)
            """, section_id=section_info.section_id, lesson_id=lesson_info.lesson_id, lesson_name=lesson_info.lesson_name)
        
        # Video node
        session.run("""
            MATCH (l:Lesson {id: $lesson_id})
            MERGE (v:Video {id: $video_id, url: $video_url})
            MERGE (l)-[:HAS_VIDEO]->(v)
            """, lesson_id=lesson_info.lesson_id, video_id=video_info.video_id, video_url=video_info.video_url)
        
                # Transcript chunks
        prev_chunk_id = None
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{video_info.video_id}_{getattr(chunk, 'chunk_id', chunk.chunk_id)}"
            # Extract all needed fields from chunk
            text = getattr(chunk, "text", chunk.text)
            start_time = getattr(chunk, "start_time", chunk.start_time)
            end_time = getattr(chunk, "end_time", chunk.end_time)
            topics = getattr(chunk, "topics", chunk.topics)
            lesson_id = getattr(chunk, "lesson_id", chunk.lesson_id)
            lesson_name = getattr(chunk, "lesson_name", chunk.lesson_name)
            section_id = getattr(chunk, "section_id", chunk.section_id)
            section_name = getattr(chunk, "section_name", chunk.section_name)
            course_id = getattr(chunk, "course_id", chunk.course_id)
            course_name = getattr(chunk, "course_name", chunk.course_name)
            video_url = getattr(chunk, "video_url", chunk.video_url)

            # MERGE node and set/update all properties
            session.run("""
                MATCH (v:Video {id: $video_id})
                MERGE (t:TranscriptChunk {id: $chunk_id})
                SET t.text = $text,
                    t.start_time = $start_time,
                    t.end_time = $end_time,
                    t.topics = $topics,
                    t.lesson_id = $lesson_id,
                    t.lesson_name = $lesson_name,
                    t.section_id = $section_id,
                    t.section_name = $section_name,
                    t.course_id = $course_id,
                    t.course_name = $course_name,
                    t.video_url = $video_url
                MERGE (v)-[:HAS_CHUNK]->(t)
                """,
                video_id=video_info.video_id,
                chunk_id=chunk_id,
                text=text,
                start_time=start_time,
                end_time=end_time,
                topics=topics,
                lesson_id=lesson_id,
                lesson_name=lesson_name,
                section_id=section_id,
                section_name=section_name,
                course_id=course_id,
                course_name=course_name,
                video_url=video_url
            )

            # 2. Sequential linking (NEXT)
            if prev_chunk_id:
                session.run("""
                    MATCH (t1:TranscriptChunk {id: $prev_id}), (t2:TranscriptChunk {id: $curr_id})
                    MERGE (t1)-[:NEXT]->(t2)
                    """, prev_id=prev_chunk_id, curr_id=chunk_id)
            prev_chunk_id = chunk_id

            # 3. Semantic/topic/entity linking (NER/classification results)
            # Assume chunk.topics is a list of strings like ["Diabetes", "Steroid"]
            topics =chunk.topics
            if topics:
                for topic in topics:
                    session.run("""
                        MERGE (topic:Topic {name: $topic})
                        WITH topic
                        MATCH (t:TranscriptChunk {id: $chunk_id})
                        MERGE (t)-[:MENTIONS]->(topic)
                        """, topic=topic, chunk_id=chunk_id)

