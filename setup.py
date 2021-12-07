from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in razorpay_integration/__init__.py
from razorpay_integration import __version__ as version

setup(
	name="razorpay_integration",
	version=version,
	description="Razorpay Integration for frappe",
	author="Frappe",
	author_email="developers@frappe.io",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
