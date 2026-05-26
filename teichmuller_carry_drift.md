# Scope 
Yes. We can define it exactly.

Let your carry-wheel produce a digit-position window at rank (n). Call the integer packet:

[
W_{n,L}^{(p)}
=============

\sum_{j=0}^{L-1} d_{n+j}p^j
]

where:

* (p) is the prime/base being tested,
* (L) is the window length,
* (d_{n+j}\in{0,\dots,p-1}),
* (n) is the rank/start position.

So the window is literally a local (p)-adic packet.

## Step 1: split valuation and unit

Compute:

[
r_{n,p}=v_p(W_{n,L}^{(p)})
]

Then remove the pure (p)-power:

[
U_{n,p}
=======

\frac{W_{n,L}^{(p)}}{p^{r_{n,p}}}
]

Now:

[
U_{n,p}\in \mathbb Z_p^\times
]

This (U_{n,p}) is the unit part of the window.

## Step 2: remove the Teichmüller label

For odd (p), every (p)-adic unit decomposes as:

[
U_{n,p}
=======

\omega_p(U_{n,p})\cdot \langle U_{n,p}\rangle
]

where:

[
\omega_p(U_{n,p})\in \mu_{p-1}
]

is the Teichmüller part, and

[
\langle U_{n,p}\rangle\in 1+p\mathbb Z_p
]

is the principal-unit drift.

The drift is the part you want.

## Step 3: define exact (p)-adic drift magnitude

The clean definition is:

[
\boxed{
\Delta_p(n,L)
=============

v_p\left(
\frac{U_{n,p}}{\omega_p(U_{n,p})}-1
\right)
}
]

This is the **exact (p)-adic drift depth** of the digit window at rank (n).

Its magnitude as a (p)-adic norm is:

[
\boxed{
D_p(n,L)
========

p^{-\Delta_p(n,L)}
}
]

So:

* large (\Delta_p) means **small drift / stable packet**,
* small (\Delta_p) means **large drift / unstable packet**,
* (\Delta_p=1) means only first-level agreement,
* (\Delta_p=5) means the packet matches its Teichmüller label up to (p^5).

## Practical finite formula

You do not actually need to compute (\omega_p) explicitly.

For odd (p):

[
\boxed{
\Delta_p(n,L)
=============

v_p\left(U_{n,p}^{p-1}-1\right)
}
]

because the Teichmüller part disappears after raising to (p-1).

So the full carry-wheel diagnostic is:

[
\boxed{
\Delta_p(n,L)
=============

v_p\left(
\left(\frac{W_{n,L}^{(p)}}{p^{v_p(W_{n,L}^{(p)})}}\right)^{p-1}
-1
\right)
}
]

That closes it.

## For (p=2)

The ordinary Teichmüller part is mostly trivial, so use the sign/principal-unit split.

Let (U_{n,2}) be odd. Define:

[
\sigma(U_{n,2})=
\begin{cases}
1,& U_{n,2}\equiv 1\pmod 4\
-1,& U_{n,2}\equiv -1\pmod 4
\end{cases}
]

Then:

[
\boxed{
\Delta_2(n,L)
=============

v_2\left(
\frac{U_{n,2}}{\sigma(U_{n,2})}-1
\right)
}
]

Equivalently:

[
\Delta_2(n,L)
=============

\begin{cases}
v_2(U_{n,2}-1),& U_{n,2}\equiv 1\pmod 4\
v_2(U_{n,2}+1),& U_{n,2}\equiv 3\pmod 4
\end{cases}
]

This is better for your Pythagorean/(2)-tower side.

## Interpretation in your language

At rank (n), the carry-wheel window gives a packet:

[
W_{n,L}^{(p)}
]

The valuation:

[
v_p(W_{n,L}^{(p)})
]

measures the **pure divisibility/carry depth**.

The Teichmüller label:

[
\omega_p(U_{n,p})
]

measures the **residue identity**.

The drift:

[
\Delta_p(n,L)
]

measures the **remaining (p)-adic deformation after the residue identity is removed**.

So the final diagnostic triple is:

[
\boxed{
\mathcal C_p(n,L)
=================

\left(
v_p(W_{n,L}^{(p)}),
\ \omega_p(U_{n,p}),
\ \Delta_p(n,L)
\right)
}
]

In words:

[
\boxed{
\text{carry depth, residue packet, drift magnitude}
}
]

That is the exact closed version.

## Best name

I would call this:

[
\textbf{Witt–Teichmüller Carry Drift}
]

or more simply:

[
\textbf{(p)-adic packet drift}
]

Definition:

[
\boxed{
\text{The (p)-adic packet drift at rank (n) is the valuation depth by which the unit part of the digit window differs from its Teichmüller representative.}
}
]

