## Support Information 

For reporting on security, bug reports, or to contact the maintainers, feel free to fill out our [Support Form](https://docs.google.com/forms/d/e/1FAIpQLSfnR0p3P9GXqE0vYL3POOB-4eRcw-czH4RW3DlPySVc50C3LQ/viewform?usp=header)

Open up an [issue](https://github.com/tiva710/SE_Project_2/issues) for timely help as well!

### Common Installation Errors (Frontend)

These errors are in regards to the installation steps documented in [INSTALL.md](https://github.com/tiva710/SE_Project_2/blob/main/docs/INSTALL.md)

1. ```npm install``` fails

&emsp;Problem: Missing or outdated Node.js/npm version.

&emsp;Solution:

&emsp;&emsp;Run npm install -g npm to update npm.

&emsp;&emsp;Delete node_modules and package-lock.json and run npm install again.

2. ```npm run dev``` fails

&emsp;Problem: Port already in use or missing dependencies.

&emsp;Solution:

&emsp;&emsp;Check if port 5173 (default Vite dev server) is in use. Kill conflicting process or change the port:

&emsp;&emsp;```npm run dev -- --port 5174```

&emsp;&emsp;Ensure all dependencies installed successfully. Run ```npm install``` again if needed.

3. Browser or Hot Reload Issues

&emsp;Problem: Styles or UI not updating.

&emsp;Solution:

&emsp;&emsp;Clear browser cache.

&emsp;&emsp;Restart ```npm run dev```.

&emsp;&emsp;Delete node_modules/.vite cache folder.

---

For running frontend tests, please refer to [TESTS.md](https://github.com/tiva710/SE_Project_2/blob/main/docs/TESTS.md)
