###################################################
#
# chunk_list: Given a master list and a preferred
#             number of sections, chunk the list
#             into roughly-equal sized sections
#             and return a list containing all
#             sub-list sections.
# 
def chunk_list(master_list,n_sec):
    master_len = len(master_list)
    # Number of sections containing master_len//n_sec + 1 elements
    n_bump_sublist = master_len % n_sec
    bump_len = master_len//n_sec + 1
    # Number of sections containing master_len//n_sec elements
    n_base_sublist = n_sec - n_bump_sublist
    base_len = master_len//n_sec
    # Initialize sub_lists
    sub_lists=[]
    idx_beg=-9
    idx_end=-9
    idx_start=0
    # Chunk through bump-lists (sub-lists containing an additional element)
    for i in range(n_bump_sublist):
        idx_beg = 0 + i*bump_len
        idx_end = idx_beg + bump_len
        chunk = master_list[idx_beg:idx_end]
        sub_lists.append(chunk)
        idx_start = idx_end
    # chunk through base-lists (sub-lists containing base_len elements)
    for i in range(n_base_sublist):
        idx_beg = idx_start + i*base_len
        idx_end = idx_beg + base_len
        chunk = master_list[idx_beg:idx_end]
        sub_lists.append(chunk)
    return sub_lists


if __name__ == "__main__":
    import datetime
    # Collect inputs (strings)
    beg_date_str = input('')
    end_date_str = input('')
    n_chunks_str = input('')
    # Convert from string where necessary
    n_chunks = int(n_chunks_str)
    # Define beginning/ending datetime
    beg_dt = datetime.datetime.strptime(beg_date_str,'%Y%m%d')
    end_dt = datetime.datetime.strptime(end_date_str,'%Y%m%d')
    # Construct total date list
    date_list = [datetime.datetime.strftime(beg_dt,'%Y%m%d')]
    cur_dt = beg_dt
    while cur_dt < end_dt:
        cur_dt = cur_dt + datetime.timedelta(days=1)
        date_list.append(datetime.datetime.strftime(cur_dt,'%Y%m%d'))
    # Generate n_chunks sub-lists from date_list
    chunked_list=chunk_list(date_list,n_chunks)
    # Print beginning/end dates of each sub-list in chunked_list
    for sublist in chunked_list:
        print(sublist[0],sublist[-1])
    
