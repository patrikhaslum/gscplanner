AC_INIT([SgtServer], [0.1], [dan.gordon@nicta.com.au])

AC_CONFIG_SRCDIR([psr_server.cc])

AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE([-Wall -Werror foreign])

LT_INIT([disable-shared])

AC_PROG_CXX([clang++ g++])
AC_LANG([C++])
AX_CXX_COMPILE_STDCXX_14([noext])
AC_SUBST([AM_CXXFLAGS], ["$AM_CXXFLAGS -Wall"])

AX_BOOST_BASE(,, [AC_MSG_ERROR([SmartGridToolbox needs Boost, but it was not found in your system])])
AX_BOOST_CHRONO
AX_BOOST_DATE_TIME
AX_BOOST_FILESYSTEM
AX_BOOST_REGEX
AX_BOOST_SYSTEM
AX_BOOST_THREAD

AC_ARG_WITH([gurobi-libs], [AS_HELP_STRING([--with-gurobi-libs=link_flag], [specify gurobi link flags])])
AC_SUBST([GUROBI_LIBS], [$with_gurobi_libs])

AC_ARG_WITH([bonmin-libs], [AS_HELP_STRING([--with-bonmin-libs=link_flag], [specify bonmin link flags])])
AC_SUBST([BONMIN_LIBS], [$with_bonmin_libs])

AC_ARG_WITH([extra-libs], [AS_HELP_STRING([--with-extra-libs=link_flag], [specify extra link flags])])
AC_SUBST([EXTRA_LIBS], [$with_extra_libs])

AC_CONFIG_FILES([Makefile])

AC_OUTPUT
