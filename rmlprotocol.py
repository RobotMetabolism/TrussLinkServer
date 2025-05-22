import struct

# Hardcoded protocol information
HEADER_LENGTH_SIZE = 1
HEADER_PKG_TYPE_SIZE = 1
HEADER_LENGTH = HEADER_LENGTH_SIZE + HEADER_PKG_TYPE_SIZE
FOOTER_LENGTH = 2

STRUCT_FORMAT_HEADER = 'B c'
STRUCT_FORMAT_SUBHEADER = 'B c'
STRUCT_FORMAT_FOOTER = 'H'

# STRUCT_FORMAT_HELLO = 'B c B B B B B B B B'
STRUCT_FORMAT_HELLO = 'B B'
STRUCT_FORMAT_ACK = 'B'
STRUCT_FORMAT_UPDATE = 'c B B B B B B B H'
STRUCT_FORMAT_CAL_CON = 'Q H H H H H H H H'
STRUCT_FORMAT_CAL = ''
STRUCT_FORMAT_POS = 'B B B B'
STRUCT_FORMAT_SIN = 'H B B h H B B h H'
STRUCT_FORMAT_WALK = 'c'
STRUCT_FORMAT_EPOCH = 'q'

STRUCT_FORMAT_LIST_ACTUAL = 'h H'

STRUCT_LENGTH_HELLO = 2
STRUCT_LENGTH_ACK = 1
STRUCT_LENGTH_UPDATE = 8
STRUCT_LENGTH_CAL_CON = 24
STRUCT_LENGTH_CAL = 0
STRUCT_LENGTH_POS = 4
STRUCT_LENGTH_SIN = 14
STRUCT_LENGTH_WALK = 1
STRUCT_LENGTH_EPOCH = 8

STRUCT_FORMATS = {
    b'H': STRUCT_FORMAT_HELLO,
    b'A': STRUCT_FORMAT_ACK,
    b'U': STRUCT_FORMAT_UPDATE,
    b'C': STRUCT_FORMAT_CAL_CON,
    b'P': STRUCT_FORMAT_POS,
    b'S': STRUCT_FORMAT_SIN,
    b'W': STRUCT_FORMAT_WALK,
    b'F': STRUCT_FORMAT_FOOTER,
    b'T': STRUCT_FORMAT_EPOCH,
}

HEADERS = {
    'A': bytes([STRUCT_LENGTH_ACK]) + b'A',
    'C': bytes([STRUCT_LENGTH_CAL]) + b'C',
    'P': bytes([STRUCT_LENGTH_POS]) + b'P',
    'S': bytes([STRUCT_LENGTH_SIN]) + b'S',
    'W': bytes([STRUCT_LENGTH_WALK]) + b'W',
    'T': bytes([STRUCT_LENGTH_EPOCH]) + b'T',
}


###################################################################################################

# Credit to https://github.com/hiharin/snappro_xboot/blob/master/board/dm3730logic/prod-id/crc-15.c

def get_crc_15(msg):
    crc = 0

    for i in range(len(msg)):
        byte = msg[i]
        for i in range(7):
            crcnext = (byte & 1) ^ (crc>>14)
            crc = (crc << 1) & 0x7fff
            if not (crcnext == 0):
                crc = crc^0x4599
            byte = byte >> 1

    # print(crc)
    return crc

###################################################################################################


class RMLPacker:

    @staticmethod
    def make_crc_footer(header_and_body):
        short_crc = get_crc_15(header_and_body)
        return int(short_crc).to_bytes(2, 'big')

    # These functions have to do with RECEIVING PACKAGES from the Link:

    @staticmethod
    def decode_header(header):
        return struct.unpack(STRUCT_FORMAT_HEADER, header)

    @staticmethod
    def decode(package_type, bin_data):
        return struct.unpack(STRUCT_FORMATS[package_type], bin_data)

    @staticmethod
    def verify_checksum(header, body, footer):
        # print(str(footer), end = " and ")
        # print(str(RMLPacker.make_crc_footer(header + body)))
        return struct.unpack('H', footer)[0] == get_crc_15(header+body)

    # These functions have to do with SENDING PACKAGES to the Link:

    @staticmethod
    def encode(package_type, data_tuple, pre_encoded=False):
        # if this is a calibration message there is no body
        if package_type == b'C':
            return b''
        return struct.pack(STRUCT_FORMATS[package_type], *data_tuple)

    @staticmethod
    def make_list_header(nr_repeat, start_time):
        return struct.pack(STRUCT_FORMAT_LIST_ACTUAL, *(nr_repeat, start_time))

    @staticmethod
    def make_calibrate_package():
        header_and_body = HEADERS['C'] + RMLPacker.encode(b'C', ())
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_position_package(srv0_pos, srv1_pos, srv0_vel, srv1_vel):
        header_and_body = HEADERS['P'] + RMLPacker.encode(b'P', (srv0_pos, srv1_pos, srv0_vel, srv1_vel,))
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_sinusoidal_package(start_time, a0, x0, ps0, p0, a1, x1, ps1, p1):
        header_and_body = HEADERS['S'] + RMLPacker.encode(b'S', (start_time, a0, x0, ps0, p0, a1, x1, ps1, p1,))
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_walk_package(nr_steps):
        header_and_body = HEADERS['W'] + RMLPacker.encode(b'W', (nr_steps,))
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_epoch_package(server_epoch):
        header_and_body = HEADERS['T'] + RMLPacker.encode(b'T', (server_epoch,))
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_ack_package(ack):
        header_and_body = HEADERS['A'] + RMLPacker.encode(b'A', (ack,))
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)

    @staticmethod
    def make_list_position(srv0_pos, srv1_pos, srv0_vel, srv1_vel, duration):
        return bytes([duration]) + b'P' + RMLPacker.encode(b'P', (srv0_pos, srv1_pos, srv0_vel, srv1_vel,))

    @staticmethod
    def make_list_sin(start_time, a0, x0, ps0, p0, a1, x1, ps1, p1, duration):
        return bytes([duration]) + b'S' + RMLPacker.encode(b'S', (start_time, a0, x0, ps0, p0, a1, x1, ps1, p1,))

    @staticmethod
    def make_list(body):
        header_and_body = bytes([len(body)]) + b'L' + body
        return header_and_body, RMLPacker.make_crc_footer(header_and_body)
