CC ?= gcc
CXX ?= g++
CFLAGS ?= -O3 -msse4.2
CXXFLAGS ?= -O3
BUILD := build

.PHONY: all clean verify reproduce-main

all: $(BUILD)/mfi_ct_spaphish $(BUILD)/dmc_ac_spaphish $(BUILD)/divide_en_10

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/mfi_ct_spaphish: src/mfi_ct_spaphish_historical.c | $(BUILD)
	$(CC) $(CFLAGS) $< -lm -o $@

$(BUILD)/dmc_ac_spaphish: src/dmc_ac_spaphish_historical.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -lm -o $@

$(BUILD)/divide_en_10: src/divide_en_10_historical.c | $(BUILD)
	$(CC) -O2 $< -o $@

verify:
	python verify_package.py

reproduce-main:
	python scripts/reproduce_main_10fold.py

clean:
	rm -rf $(BUILD)
