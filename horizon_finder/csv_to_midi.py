import csv
from mido import MidiFile, MidiTrack, Message

input_csv_file = "./test_results/G_canny_edge_horiz_data.csv"
output_midi_file = "./audio_files/output.mid"

def get_major_scales(start_note_val, num_octaves=1):
    # TODO: Minor scale option
    Minor_Scale = [0, 2, 3, 5, 7, 8, 10, 12]
    Major_Scale = [0, 2, 4, 5, 7, 9, 11, 12]

    # can be transposed
    final_scale = [start_note_val]
    for octave_ in range(0, num_octaves):
        major_scale_trans = [val+start_note_val for val in Major_Scale]
        final_scale += major_scale_trans[1:]
        start_note_val += 12

    return final_scale

C4_note_val = 60
num_octaves = 2
C_Major_C4_4_octaves = get_major_scales(C4_note_val, num_octaves=num_octaves)


def csv_to_midi(input_csv_file, output_midi_file, map_to_notes):

    mid = MidiFile()  # Create a new MIDI file
    track = MidiTrack()  # Create a new track
    mid.tracks.append(track)  # Add the track to the MIDI file

    vals = []
    max_ = -1
    min_ = -1
    with open (input_csv_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            val = int(row[0])
            vals.append(val)
            if max_ == -1 or val > max_:
                max_ = val
            if min_ == -1 or val < min_:
                min_ = val

    num_notes = len(map_to_notes)

    for val in vals:
        percent = (val - min_) / (max_ - min_)

        idx = int(percent * (num_notes-1))
        print(idx)
        note_ = map_to_notes[idx]

        # Add a note on message (e.g., Middle C, velocity 64)
        track.append(Message('note_on', note=note_, velocity=64, time=0))
        # Add a note off message after a certain time (e.g., 480 ticks)
        track.append(Message('note_off', note=note_, velocity=64, time=40))

    # Save the MIDI file
    mid.save(output_midi_file)

csv_to_midi(input_csv_file, output_midi_file, C_Major_C4_4_octaves)