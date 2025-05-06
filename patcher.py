import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import re
import shutil
import sys

# artist friendly script to patch missing frames in a sequence by duplicating the frame before each missing chunk
# useful for for previewing, or just to find missing frames
# Bruno CC - May 2025 v1.0

def main():

    file_path = prompt_file()

    if file_path:
        sequence_info = get_sequence_info(find_sequences(file_path))
        pad, existing, missing, prefix, ext = sequence_info

        display_range = f"{prefix}.{str(existing[0]).zfill(pad)} - {prefix}.{str(existing[-1]).zfill(pad)}"
        display_missing = "".join([str(f).zfill(pad) + "\n" for f in missing])
    else:
        sys.exit(0)

    def on_close():
        root.destroy()  
        sys.exit(0)     

    root = tk.Tk()
    root.title("Sequence Patcher Tool")

    desc = tk.Label(root, text = f"patch missing frames in a sequence by duplicating\nthe frame before each missing chunk")
    desc.pack(padx=30,pady=5)

    seq_label = tk.Label(root, text = f"{display_range}")
    seq_label.pack(padx=30,pady=5)

    if missing:
        missing_label = tk.Label(root, text = f"{len(missing)} missing frames found:", bg="red")
        missing_label.pack(padx=30,pady=5)

        scroll_text = ScrolledText(root, wrap=tk.WORD, width=pad*3, height=10)
        scroll_text.pack()

        def on_patch_clicked():
            success = patch_missing(sequence_info,file_path)
            
            for widget in root.winfo_children():
                widget.destroy()

            if success:
                seq_label = tk.Label(root, text = f"{display_range}")
                seq_label.pack(padx=30,pady=5)

                success_label = tk.Label(root, text = f"frames patched successfully", bg="green")
                success_label.pack(padx=30,pady=5)
            else:
                fail_label = tk.Label(root, text = f"warning: patch frames not found or not created", bg="red")
                fail_label.pack(padx=30,pady=5)

        def on_patch_subfolder_clicked():
            success = patch_missing_subfolder(sequence_info,file_path)
            
            for widget in root.winfo_children():
                widget.destroy()

            if success:
                seq_label = tk.Label(root, text = f"{display_range}")
                seq_label.pack(padx=30,pady=5)

                success_label = tk.Label(root, text = f"frames patched successfully", bg="green")
                success_label.pack(padx=30,pady=5)
            else:
                fail_label = tk.Label(root, text = f"warning: patch frames in subfolder do not match detected missing frames", bg="red")
                fail_label.pack(padx=30,pady=5)

        scroll_text.insert(tk.END, f"{display_missing}")

        patch_button = tk.Button(root,text="patch frames in same folder", command=lambda:on_patch_clicked(), bg="green", cursor="hand2")
        patch_button.pack(padx=30,pady=5)

        patch_folder_button = tk.Button(root,text="patch frames in new subfolder", command=lambda:on_patch_subfolder_clicked(), bg="green",cursor="hand2")
        patch_folder_button.pack(padx=30,pady=5)

    else:
        no_missing_label = tk.Label(root, text = f"No missing frames found in sequence", bg="green")
        no_missing_label.pack(padx=30,pady=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


#return filename and path
def prompt_file():
    
    file_path = filedialog.askopenfilename(title="Select frame from a sequence to scan for missing frames")
    if file_path:
        return Path(file_path)
    else:
        return None
    

#find frames in sequence
def find_sequences(file_path):
    pattern = re.compile(r"^(.*?)(\d+)(\.\w+)$")

    sequence = {}
    selected_file = Path(file_path)

    if selected_file.is_file():
        match = pattern.match(selected_file.name)
        if match:
            prefix, number, ext = match.groups()
            key = f"{prefix}#{ext}"
            sequence[key] = []

    for file in file_path.parent.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                prefix_n, number_n, ext_n = match.groups()
                if prefix_n == prefix and ext_n == ext:
                    sequence[key].append(number_n)

    for frames in sequence.values():
        frames.sort()
    
    return sequence


#patch missing frames with duplicates of last non-missing frame before each missing chunk
def patch_missing(sequence_info,file_path):
    pad, existing, missing, prefix, ext = sequence_info

    if missing:
        for f in missing:
            padded_frame = str(f).zfill(pad)
            if f-1 in existing:
                frame_for_copy = file_path.with_name(prefix + str(f-1).zfill(pad) + ext)
            copy_new_name = file_path.with_name(prefix + padded_frame + ext)
            shutil.copy2(frame_for_copy,copy_new_name)
        
    #check to make sure sequence is patched
    sequence_info_check = get_sequence_info(find_sequences(file_path))
    _,_,missing_check,_,_ = sequence_info_check

    if missing_check:
        return False
    return True


#patch missing frames with duplicates of last non-missing frame before each missing chunk (in a subfolder)
def patch_missing_subfolder(sequence_info,file_path):
    pad, existing, missing, prefix, ext = sequence_info

    if missing:
        subfolder_path = file_path.parent / f"{prefix}_patch_frames"
        subfolder_path.mkdir(exist_ok=True)
        for f in missing:
            padded_frame = str(f).zfill(pad)
            if f-1 in existing:
                frame_for_copy = file_path.with_name(prefix + str(f-1).zfill(pad) + ext)
            
            copy_new_name = subfolder_path / (prefix + padded_frame + ext)
            shutil.copy2(frame_for_copy,copy_new_name)
        
    #check to make sure sequence patch exists inside subfolder
    sequence_info_check = get_sequence_info(find_sequences(file_path))
    _,_,missing_check,_,_ = sequence_info_check

    sequence_info_subfolder = get_sequence_info(find_sequences(copy_new_name))
    _,existing_check_subfolder,_,_,_ = sequence_info_subfolder

    if missing_check != existing_check_subfolder:
        return False
    return True


def get_sequence_info(sequence):

    for key , frames in sequence.items():

        padding = len(frames[0])
        int_frames = [int(frame) for frame in frames]
        start, end = int_frames[0], int_frames[-1]
        full_range = set(range(start, end + 1))
        existing = set(int_frames)
        missing = sorted(full_range - existing)
        prefix , ext = key.split("#")        
    
    return (padding, sorted(list(existing)), missing, prefix, ext)


if __name__ == "__main__":
    main()

