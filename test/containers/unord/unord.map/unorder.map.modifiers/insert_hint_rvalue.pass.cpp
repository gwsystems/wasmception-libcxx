//===----------------------------------------------------------------------===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is dual licensed under the MIT and the University of Illinois Open
// Source Licenses. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

// <unordered_map>

// template <class Key, class T, class Hash = hash<Key>, class Pred = equal_to<Key>,
//           class Alloc = allocator<pair<const Key, T>>>
// class unordered_map

// template <class P,
//           class = typename enable_if<is_convertible<P, value_type>::value>::type>
//     iterator insert(const_iterator p, P&& x);

#if _LIBCPP_DEBUG2 >= 1
#define _LIBCPP_ASSERT(x, m) ((x) ? (void)0 : std::exit(0))
#endif

#include <unordered_map>
#include <cassert>

#include "../../../MoveOnly.h"
#include "../../../min_allocator.h"

int main()
{
    {
        typedef std::unordered_map<double, int> C;
        typedef C::iterator R;
        typedef std::pair<double, short> P;
        C c;
        C::const_iterator e = c.end();
        R r = c.insert(e, P(3.5, 3));
        assert(c.size() == 1);
        assert(r->first == 3.5);
        assert(r->second == 3);

        r = c.insert(c.end(), P(3.5, 4));
        assert(c.size() == 1);
        assert(r->first == 3.5);
        assert(r->second == 3);

        r = c.insert(c.end(), P(4.5, 4));
        assert(c.size() == 2);
        assert(r->first == 4.5);
        assert(r->second == 4);

        r = c.insert(c.end(), P(5.5, 4));
        assert(c.size() == 3);
        assert(r->first == 5.5);
        assert(r->second == 4);
    }
#ifndef _LIBCPP_HAS_NO_RVALUE_REFERENCES
    {
        typedef std::unordered_map<MoveOnly, MoveOnly> C;
        typedef C::iterator R;
        typedef std::pair<MoveOnly, MoveOnly> P;
        C c;
        C::const_iterator e = c.end();
        R r = c.insert(e, P(3, 3));
        assert(c.size() == 1);
        assert(r->first == 3);
        assert(r->second == 3);

        r = c.insert(c.end(), P(3, 4));
        assert(c.size() == 1);
        assert(r->first == 3);
        assert(r->second == 3);

        r = c.insert(c.end(), P(4, 4));
        assert(c.size() == 2);
        assert(r->first == 4);
        assert(r->second == 4);

        r = c.insert(c.end(), P(5, 4));
        assert(c.size() == 3);
        assert(r->first == 5);
        assert(r->second == 4);
    }
#endif  // _LIBCPP_HAS_NO_RVALUE_REFERENCES
#if __cplusplus >= 201103L
    {
        typedef std::unordered_map<double, int, std::hash<double>, std::equal_to<double>,
                            min_allocator<std::pair<const double, int>>> C;
        typedef C::iterator R;
        typedef std::pair<double, short> P;
        C c;
        C::const_iterator e = c.end();
        R r = c.insert(e, P(3.5, 3));
        assert(c.size() == 1);
        assert(r->first == 3.5);
        assert(r->second == 3);

        r = c.insert(c.end(), P(3.5, 4));
        assert(c.size() == 1);
        assert(r->first == 3.5);
        assert(r->second == 3);

        r = c.insert(c.end(), P(4.5, 4));
        assert(c.size() == 2);
        assert(r->first == 4.5);
        assert(r->second == 4);

        r = c.insert(c.end(), P(5.5, 4));
        assert(c.size() == 3);
        assert(r->first == 5.5);
        assert(r->second == 4);
    }
#ifndef _LIBCPP_HAS_NO_RVALUE_REFERENCES
    {
        typedef std::unordered_map<MoveOnly, MoveOnly, std::hash<MoveOnly>, std::equal_to<MoveOnly>,
                            min_allocator<std::pair<const MoveOnly, MoveOnly>>> C;
        typedef C::iterator R;
        typedef std::pair<MoveOnly, MoveOnly> P;
        C c;
        C::const_iterator e = c.end();
        R r = c.insert(e, P(3, 3));
        assert(c.size() == 1);
        assert(r->first == 3);
        assert(r->second == 3);

        r = c.insert(c.end(), P(3, 4));
        assert(c.size() == 1);
        assert(r->first == 3);
        assert(r->second == 3);

        r = c.insert(c.end(), P(4, 4));
        assert(c.size() == 2);
        assert(r->first == 4);
        assert(r->second == 4);

        r = c.insert(c.end(), P(5, 4));
        assert(c.size() == 3);
        assert(r->first == 5);
        assert(r->second == 4);
    }
#endif  // _LIBCPP_HAS_NO_RVALUE_REFERENCES
#if _LIBCPP_DEBUG2 >= 1
    {
        typedef std::unordered_map<double, int> C;
        typedef C::iterator R;
        typedef C::value_type P;
        C c;
        C c2;
        C::const_iterator e = c2.end();
        R r = c.insert(e, P(3.5, 3));
        assert(false);
    }
#endif
#endif
}
