import streamlit as st
import multiprocessing as mp
import time


def process_func(queue):
    for i in range(10):
        time.sleep(1)
        queue.put(f"Task progress: {i+1}/10")
    queue.put("Task completed.")


def main():
    st.set_page_config(page_title="Shared session_state demo")
    session_state = st.session_state.setdefault('session_state', {'logs': []})
    queue = mp.Queue()
    p = mp.Process(target=process_func, args=(queue,))
    p.start()

    st.write("Task progress:")
    while True:
        try:
            log = queue.get(block=False)
            session_state.logs.append(log)
        except Exception as e:
            print(e)
            pass
        for log in session_state.logs:
            st.write(log)
        if session_state.logs and session_state.logs[-1] == "Task completed.":
            p.join()
            st.success("Task completed!")
            break


if __name__ == '__main__':
    main()
