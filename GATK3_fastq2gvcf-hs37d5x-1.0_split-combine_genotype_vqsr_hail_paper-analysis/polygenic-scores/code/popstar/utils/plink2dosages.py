#!/usr/bin/env python3
import csv


def convert_bed_to_dosages(bfile_prefix, out_path):
    with open(out_path, 'wt') as out_file:
        out_file.write('vid')
        n_samples = 0
        with open(bfile_prefix + '.fam', 'rt') as fam_file:
            for line in fam_file:
                _, iid, _, _, _, _ = line.rstrip().split()
                assert iid != '' and iid != '0', 'Invalid line encountered in FAM file; check for trailing blank lines or IID = 0'
                n_samples += 1
                out_file.write('\t' + iid)
        out_file.write('\n')

        with open(bfile_prefix + '.bed', 'rb') as bed_file:
            magic = bed_file.read(3)
            assert magic == b'\x6c\x1b\x01', 'BED file has incorrect magic string; PLINK variant-major bed files only supported'

            with open(bfile_prefix + '.bim', 'rt') as bim_file:
                for line in bim_file:
                    _, vid, _, _, allele1, allele2 = line.rstrip().split()
                    vid_parts = vid.split(':')
                    assert len(vid_parts) == 4, 'Variant ID in BIM file could not be parsed; only PLINK files generated by Hail are supported'
                    _, _, vid_ref, vid_alt = vid.split(':')
                    assert (allele1 == vid_alt and allele2 == vid_ref) or (allele1 == vid_ref and allele2 == vid_alt), 'Variant ID and alleles do not match in BIM file; only PLINK files generated by Hail are supported'
                    allele1_is_alt = allele1 == vid_alt
                    
                    out_file.write(vid + '\t')

                    genotype_byte = None
                    genotype_byte_pos = 4
                    for sample_i in range(n_samples):
                        if genotype_byte_pos == 4:
                            genotype_byte = bed_file.read(1)[0]
                            genotype_byte_pos = 0
                        genotype_code = genotype_byte & 0b11
                        if genotype_code == 0b00:      # Homozygous for allele 1
                            if allele1_is_alt:
                                out_file.write('2')
                            else:
                                out_file.write('0')
                        elif genotype_code == 0b01:    # Missing
                            out_file.write('.')
                        elif genotype_code == 0b10:    # Heterozygous
                            out_file.write('1')
                        else:                          # Homozygous for allele 2
                            if allele1_is_alt:
                                out_file.write('0')
                            else:
                                out_file.write('2')

                        genotype_byte >>= 2
                        genotype_byte_pos += 1
                    
                    out_file.write('\n')


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        sys.exit('Usage: plink2dosages.py <bfile_prefix> <out_file>')

    convert_bed_to_dosages(sys.argv[1], sys.argv[2])
