import { useEffect } from 'react';
import { useRouter } from 'next/router';

const IndexPage: React.FC = () => {
    const router = useRouter();

    useEffect(() => {
        router.replace('/login');
    }, [router]);

    return null;
};

export default IndexPage;
