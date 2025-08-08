import csv
from mido import MidiFile, MidiTrack, Message


def get_major_scales(start_note_val, num_octaves=1):
    Major_Scale = [0, 2, 4, 5, 7, 9, 11, 12]

    final_scale = [start_note_val]
    for _ in range(0, num_octaves):
        major_scale_trans = [val + start_note_val for val in Major_Scale]
        final_scale += major_scale_trans[1:]
        start_note_val += 12

    return final_scale


def csv_to_midi(input_csv_file: str, output_midi_file: str, map_to_notes: list[int]):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    vals = []
    max_ = None
    min_ = None
    with open(input_csv_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            val = int(row[0])
            vals.append(val)
            max_ = val if max_ is None or val > max_ else max_
            min_ = val if min_ is None or val < min_ else min_

    if not vals:
        mid.save(output_midi_file)
        return

    num_notes = len(map_to_notes)
    if num_notes == 0:
        mid.save(output_midi_file)
        return

    span = max(1, (max_ - min_))
    for val in vals:
        percent = (val - min_) / span
        idx = int(percent * (num_notes - 1))
        note_ = map_to_notes[idx]

        track.append(Message("note_on", note=note_, velocity=64, time=0))
        track.append(Message("note_off", note=note_, velocity=64, time=40))

    mid.save(output_midi_file)


if __name__ == "__main__":
    # Example CLI usage
    C4_note_val = 60
    num_octaves = 2
    C_major = get_major_scales(C4_note_val, num_octaves=num_octaves)
    # csv_to_midi("./path/to/input.csv", "./path/to/output.mid", C_major)