/** @type {import('next').NextConfig} */
const nextConfig = {
    async redirects() {
        return [
            {
                source: '/',
                destination: '/camera',
                permanent: false,
            },
            {
                source: '/auth',
                destination: '/camera',
                permanent: false,
                missing: [
                    {
                        type: 'cookie',
                        key: 'authToken',
                    },
                ],
            },
        ];
    },
};

export default nextConfig;