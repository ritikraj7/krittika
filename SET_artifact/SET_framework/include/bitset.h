#ifndef BITSET_H
#define BITSET_H

#include <bitset>
#include <cstdint>
#include <initializer_list>
#include <iostream>
#include <vector>

#define FOR_BITSET(var, set) for(Bitset::bitlen_t var = set.first(); var != set.max_size(); var = set.next(var))

class Bitset: private std::bitset<255>{
public:
	typedef std::uint8_t bitlen_t;
private:
	typedef std::bitset<255> std_bs;
	// std::int64_t bits[4];
public:
	Bitset()=default;
	explicit Bitset(bitlen_t bit);
	Bitset(std::initializer_list<bitlen_t> bits);
	Bitset(std::vector<std::uint8_t> list);
	bitlen_t count() const;
	// Undefined behaviour if bitset is empty.
	bitlen_t first() const;
	// Returns 0 if there is no next.
	bitlen_t next(bitlen_t bit) const;
	bool contains(bitlen_t bit) const;
	void set(bitlen_t bit);
	void reset(bitlen_t bit);
	void clear();
	bitlen_t max_size() const;
	Bitset& operator|=(const Bitset& other);
	bool operator==(const Bitset& other) const;
	//Bitset& operator|=(bitlen_t other);
	friend std::ostream& operator<<(std::ostream& os, const Bitset& set);
};

#endif // BITSET_H
